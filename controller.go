package main

import (
	"context"
	"fmt"
	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/ebitenutil"
	"github.com/hajimehoshi/ebiten/v2/vector"
	"github.com/operators/rover/controller"
	"log"
	"net"
	"os"
)

const (
	screenWidth  = 600
	screenHeight = 400

	buttonSize = float32(40)

	//serverHost   = "us1.localto.net:53012"

	// serverHost = "10.0.0.65:8000"
	// streamHost = "10.0.0.65:8080"

	// serverHost = "192.168.0.170:8000"

	serverHost = "10.0.0.104:8000"
	streamHost = "10.0.0.104:8080"

	listenHost = "0.0.0.0:9000"
)

type Game struct {
	controller *controller.Game
}

func (g *Game) Update() error {
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyArrowUp), "move", "forward")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyArrowDown), "move", "backward")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyArrowLeft), "move", "left")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyArrowRight), "move", "right")

	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyR), "listen", "start")

	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyH), "camera", "left")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyL), "camera", "right")

	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyQ), "arm", "rotate:right")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyW), "arm", "rotate:left")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyA), "arm", "shoulder:up")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyS), "arm", "shoulder:down")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyZ), "arm", "elbow:bend")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyX), "arm", "elbow:extend")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyI), "arm", "wrist_pitch:up")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyK), "arm", "wrist_pitch:down")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyJ), "arm", "wrist_roll:clockwise")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyM), "arm", "wrist_roll:counterclockwise")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyN), "arm", "gripper:open")
	g.controller.UpdateButtonState(ebiten.IsKeyPressed(ebiten.KeyB), "arm", "gripper:close")

	return nil
}

func (g *Game) Draw(screen *ebiten.Image) {
	colors := g.controller.ButtonColors()
	for key, pos := range g.controller.ButtonPositions() {
		keyColor := colors[key]
		col := keyColor[1]
		if g.controller.ButtonStates()[key] {
			col = keyColor[0]
		}
		vector.DrawFilledRect(screen, pos[0], pos[1], buttonSize, buttonSize, col, true)
	}

	visualInfo := fmt.Sprintf("Visual: %s", g.controller.SensorData.Visual)
	ebitenutil.DebugPrintAt(screen, visualInfo, 10, 10)

	distanceInfo := fmt.Sprintf("Distance: %.2f%s", g.controller.SensorData.Distance, g.controller.SensorData.DistanceUnits)
	ebitenutil.DebugPrintAt(screen, distanceInfo, 10, 25)

	temperatureInfo := fmt.Sprintf("Temperature: %.2f%s", g.controller.SensorData.Temperature, g.controller.SensorData.TemperatureUnits)
	ebitenutil.DebugPrintAt(screen, temperatureInfo, 10, 40)

	humidityInfo := fmt.Sprintf("Humidity: %.2f%s", g.controller.SensorData.Humidity, g.controller.SensorData.HumidityUnits)
	ebitenutil.DebugPrintAt(screen, humidityInfo, 10, 55)

	locationInfo := fmt.Sprintf("Location: %.2f%s, %.2f%s", g.controller.SensorData.Latitude, g.controller.SensorData.LatitudeUnits, g.controller.SensorData.Longitude, g.controller.SensorData.LongitudeUnits)
	ebitenutil.DebugPrintAt(screen, locationInfo, 10, 70)
}

func (g *Game) Layout(outsideWidth, outsideHeight int) (int, int) {
	return screenWidth, screenHeight
}

func dialServer(serverHost, listenHost string) (net.Conn, error) {
	udpServerAddr, err := net.ResolveUDPAddr("udp", serverHost)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error resolving server UDP address: %v\n", err)
		return nil, err
	}

	udpLocalAddr, err := net.ResolveUDPAddr("udp", listenHost)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error resolving local UDP address: %v\n", err)
		return nil, err
	}

	return net.DialUDP("udp", udpLocalAddr, udpServerAddr)
}

func main() {
	conn, err := dialServer(serverHost, listenHost)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error dialing UDP: %v\n", err)
		return
	}
	defer conn.Close()

	gameController := controller.NewGameController(conn)
	game := &Game{controller: gameController}

	go game.controller.StreamSensorData(context.Background())
	//browser.OpenVideoStreamChrome(streamHost)

	ebiten.SetWindowSize(screenWidth, screenHeight)
	ebiten.SetWindowTitle("Cloud Rover Controller")
	if err = ebiten.RunGame(game); err != nil {
		log.Fatal("Failed to run controller:", err)
	}
}
