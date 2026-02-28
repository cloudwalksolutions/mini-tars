package controller

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"image/color"
	"net"
	"os"
	"sync"
)

const (
	screenWidth  = 600
	screenHeight = 400
)

var (
	actionGroups = map[string]ActionGroup{
		"move": {
			ActiveColor:   color.RGBA{R: 255, G: 223, B: 0, A: 255},
			InactiveColor: color.RGBA{R: 0, G: 0, B: 255, A: 255},
			Actions: []Action{
				{Name: "forward"},
				{Name: "backward"},
				{Name: "left"},
				{Name: "right"},
			},
		},
		"listen": {
			ActiveColor:   color.RGBA{R: 255, G: 0, B: 0, A: 255},
			InactiveColor: color.RGBA{R: 128, G: 128, B: 128, A: 255},
		},
		"camera": {
			ActiveColor:   color.RGBA{R: 0, G: 255, B: 0, A: 255},
			InactiveColor: color.RGBA{R: 128, G: 128, B: 0, A: 255},
			Actions: []Action{
				{Name: "left"},
				{Name: "right"},
			},
		},
		"arm": {
			ActiveColor:   color.RGBA{R: 255, G: 128, B: 0, A: 255},
			InactiveColor: color.RGBA{R: 128, G: 128, B: 0, A: 255},
			Actions: []Action{
				{Name: "rotate:right"},
				{Name: "rotate:left"},
				{Name: "shoulder:up"},
				{Name: "shoulder:down"},
				{Name: "elbow:bend"},
				{Name: "elbow:extend"},
				{Name: "wrist_pitch:up"},
				{Name: "wrist_pitch:down"},
				{Name: "wrist_roll:clockwise"},
				{Name: "wrist_roll:counterclockwise"},
				{Name: "gripper:open"},
				{Name: "gripper:close"},
			},
		},
	}
	buttonSize = float32(40.0)

	buttonPositions = map[string][2]float32{
		"move:forward":  {screenWidth/2 - buttonSize/2, screenHeight/2 - 50 - buttonSize/2},
		"move:backward": {screenWidth/2 - buttonSize/2, screenHeight/2 + 50 - buttonSize/2},
		"move:left":     {screenWidth/2 - 50 - buttonSize/2, screenHeight/2 - buttonSize/2},
		"move:right":    {screenWidth/2 + 50 - buttonSize/2, screenHeight/2 - buttonSize/2},

		"listen": {screenWidth - buttonSize*2 - 90, screenHeight - buttonSize - 20},

		"camera:left":  {screenWidth - buttonSize*2 - 30, screenHeight - buttonSize - 20}, // Placed 20 pixels from the bottom, and 30 pixels plus button size from the right edge
		"camera:right": {screenWidth - buttonSize - 20, screenHeight - buttonSize - 20},   // Placed 20 pixels from the bottom and right edges

		"arm:rotate:right":                {screenWidth - buttonSize*2 - 30, 20},
		"arm:rotate:left":                 {screenWidth - buttonSize - 20, 20},
		"arm:shoulder:up":                 {screenWidth - buttonSize*2 - 30, 70},
		"arm:shoulder:down":               {screenWidth - buttonSize - 20, 70},
		"arm:elbow:bend":                  {screenWidth - buttonSize*2 - 30, 120},
		"arm:elbow:extend":                {screenWidth - buttonSize - 20, 120},
		"arm:wrist_pitch:up":              {screenWidth - buttonSize*2 - 30, 170},
		"arm:wrist_pitch:down":            {screenWidth - buttonSize - 20, 170},
		"arm:wrist_roll:clockwise":        {screenWidth - buttonSize*2 - 30, 220},
		"arm:wrist_roll:counterclockwise": {screenWidth - buttonSize - 20, 220},
		"arm:gripper:open":                {screenWidth - buttonSize*2 - 30, 270},
		"arm:gripper:close":               {screenWidth - buttonSize - 20, 270},
	}
)

type ActionGroup struct {
	Actions       []Action
	ActiveColor   color.RGBA
	InactiveColor color.RGBA
}

type Action struct {
	Name string
}

type SensorData struct {
	Visual string `json:"visual,omitempty"`

	Temperature      float64 `json:"temperature,omitempty"`
	TemperatureUnits string  `json:"temperatureUnits,omitempty"`

	Humidity      float64 `json:"humidity,omitempty"`
	HumidityUnits string  `json:"humidityUnits,omitempty"`

	Latitude       float64 `json:"latitude,omitempty"`
	LatitudeUnits  string  `json:"latitudeUnits,omitempty"`
	Longitude      float64 `json:"longitude,omitempty"`
	LongitudeUnits string  `json:"longitudeUnits,omitempty"`

	Distance      float64 `json:"distance,omitempty"`
	DistanceUnits string  `json:"distanceUnits,omitempty"`
}

type Game struct {
	conn net.Conn

	buttonColors    map[string][2]color.RGBA
	buttonStates    map[string]bool
	buttonPositions map[string][2]float32

	SensorData  SensorData
	streamLock  sync.RWMutex
	isStreaming bool
}

func NewGameController(conn net.Conn) *Game {
	buttonColors := make(map[string][2]color.RGBA)
	buttonStates := make(map[string]bool)

	for name, group := range actionGroups {
		if len(group.Actions) == 0 {
			buttonColors[name] = [2]color.RGBA{group.ActiveColor, group.InactiveColor}
			buttonStates[name] = false
			continue
		}

		for _, button := range group.Actions {
			buttonColors[name+":"+button.Name] = [2]color.RGBA{group.ActiveColor, group.InactiveColor}
			buttonStates[name+":"+button.Name] = false
		}
	}

	return &Game{
		conn:            conn,
		buttonColors:    buttonColors,
		buttonStates:    buttonStates,
		buttonPositions: buttonPositions,
	}
}

func (g *Game) StreamSensorData(ctx context.Context) {
	g.streamLock.Lock()
	g.isStreaming = true
	g.streamLock.Unlock()

	if err := g.SendCommand("sensor", "start"); err != nil {
		return
	}

	for {
		if err := g.ReadSensorData(); err != nil {
			if errors.Is(err, os.ErrDeadlineExceeded) {
				continue
			}

			return
		}

		select {
		case <-ctx.Done():
			g.streamLock.Lock()
			g.isStreaming = false
			g.streamLock.Unlock()
			return
		default:
		}
	}
}

func (g *Game) ReadSensorData() error {
	buffer := make([]byte, 1024)
	n, err := g.conn.Read(buffer)
	if err != nil {
		return err
	}

	var data SensorData
	if err = json.Unmarshal(buffer[:n], &data); err != nil {
		return err
	}

	g.SensorData = data
	return nil
}

func (g *Game) SendCommand(actionType, action string) error {
	command := fmt.Sprintf("%s:%s", actionType, action)
	_, err := g.conn.Write([]byte(command))
	return err
}

func (g *Game) UpdateButtonState(newState bool, actionType, action string) {
	if newState && !g.IsActive(actionType, action) {
		g.SendCommand(actionType, action)
	} else if !newState && g.IsActive(actionType, action) {
		g.SendCommand(actionType, "stop")
	}

	label := fmt.Sprintf("%s:%s", actionType, action)

	for name, group := range actionGroups {
		if name == actionType {
			if len(group.Actions) == 0 {
				label = actionType
			}
			break
		}
	}

	g.buttonStates[label] = newState
}

func (g *Game) IsActive(actionType, action string) bool {
	return g.buttonStates[actionType+":"+action] || g.buttonStates[actionType]
}

func (g *Game) IsListening() bool {
	return g.buttonStates["listen"]
}

func (g *Game) IsStreaming() bool {
	g.streamLock.RLock()
	defer g.streamLock.RUnlock()

	return g.isStreaming
}

func (g *Game) ButtonStates() map[string]bool {
	return g.buttonStates
}

func (g *Game) ButtonColors() map[string][2]color.RGBA {
	return g.buttonColors
}

func (g *Game) ButtonPositions() map[string][2]float32 {
	return g.buttonPositions
}
