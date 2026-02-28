package controller_test

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"
	"github.com/operators/rover/controller"
	"os"
	"time"
)

var _ = Describe("Controller", func() {

	var (
		game          *controller.Game
		mockUDPClient = &controller.MockUDPClient{}
	)

	BeforeEach(func() {
		game = controller.NewGameController(mockUDPClient)
		Expect(game).NotTo(BeNil())

		Expect(game.IsListening()).To(BeFalse())
		Expect(game.IsStreaming()).To(BeFalse())

		Expect(game.ButtonStates()).NotTo(BeEmpty())
	})

	AfterEach(func() {
		mockUDPClient.Reset()
	})

	Context("Sending commands", func() {

		It("can return an error if unable to write", func() {
			mockUDPClient.NumCalledWrite = 1
			mockUDPClient.WriteError = errors.New("write error")

			err := game.SendCommand("move", "stop")

			Expect(err).To(MatchError("write error"))
		})

		It("can send a command", func() {
			game.SendCommand("move", "stop")
			Expect(mockUDPClient.NumCalledWrite).To(Equal(1))
			Expect(mockUDPClient.CalledWriteWithBytes).To(Equal([]byte("move:stop")))
		})

	})

	Context("Buttons", func() {

		It("can get the button colors", func() {
			Expect(game.ButtonColors()).NotTo(BeEmpty())
			Expect(game.ButtonColors()["move:forward"]).NotTo(BeEmpty())
		})

		It("can get the button positions", func() {
			buttonPositions := game.ButtonPositions()
			Expect(buttonPositions).NotTo(BeEmpty())
			Expect(buttonPositions["move:forward"]).To(Equal([2]float32{280, 130}))
			Expect(buttonPositions["move:backward"]).To(Equal([2]float32{280, 230}))
			Expect(buttonPositions["move:left"]).To(Equal([2]float32{230, 180}))
			Expect(buttonPositions["move:right"]).To(Equal([2]float32{330, 180}))

			Expect(buttonPositions["listen"]).To(Equal([2]float32{430, 340}))

			Expect(buttonPositions["camera:left"]).To(Equal([2]float32{490, 340}))
			Expect(buttonPositions["camera:right"]).To(Equal([2]float32{540, 340}))

			Expect(buttonPositions["arm:rotate:right"]).To(Equal([2]float32{490, 20}))
			Expect(buttonPositions["arm:rotate:left"]).To(Equal([2]float32{540, 20}))
			Expect(buttonPositions["arm:shoulder:up"]).To(Equal([2]float32{490, 70}))
			Expect(buttonPositions["arm:shoulder:down"]).To(Equal([2]float32{540, 70}))
			Expect(buttonPositions["arm:elbow:bend"]).To(Equal([2]float32{490, 120}))
			Expect(buttonPositions["arm:elbow:extend"]).To(Equal([2]float32{540, 120}))
			Expect(buttonPositions["arm:wrist_pitch:up"]).To(Equal([2]float32{490, 170}))
			Expect(buttonPositions["arm:wrist_pitch:down"]).To(Equal([2]float32{540, 170}))
			Expect(buttonPositions["arm:wrist_roll:clockwise"]).To(Equal([2]float32{490, 220}))
			Expect(buttonPositions["arm:wrist_roll:counterclockwise"]).To(Equal([2]float32{540, 220}))
			Expect(buttonPositions["arm:gripper:open"]).To(Equal([2]float32{490, 270}))
			Expect(buttonPositions["arm:gripper:close"]).To(Equal([2]float32{540, 270}))
		})

		It("can tell if an action is active", func() {
			Expect(game.IsActive("move", "forward")).To(BeFalse())
			game.UpdateButtonState(true, "move", "forward")
			Expect(game.IsActive("move", "forward")).To(BeTrue())
		})

		It("sends start commands when a move button is pressed", func() {
			game.UpdateButtonState(true, "move", "forward")
			Expect(game.ButtonStates()["move:forward"]).To(BeTrue())
			Expect(mockUDPClient.NumCalledWrite).To(Equal(1))
			Expect(mockUDPClient.CalledWriteWithBytes).To(Equal([]byte("move:forward")))

			game.UpdateButtonState(true, "move", "forward")
			Expect(game.ButtonStates()["move:forward"]).To(BeTrue())
			Expect(mockUDPClient.NumCalledWrite).To(Equal(1))
		})

		It("sends stop commands when a move button is released", func() {
			game.UpdateButtonState(true, "move", "forward")

			game.UpdateButtonState(false, "move", "forward")
			Expect(mockUDPClient.NumCalledWrite).To(Equal(2))
			Expect(mockUDPClient.CalledWriteWithBytes).To(Equal([]byte("move:stop")))

			game.UpdateButtonState(false, "move", "forward")
			Expect(mockUDPClient.NumCalledWrite).To(Equal(2))
		})

		It("sends listen commands when the record button is pressed", func() {
			game.UpdateButtonState(true, "listen", "start")
			Expect(mockUDPClient.NumCalledWrite).To(Equal(1))
			Expect(mockUDPClient.CalledWriteWithBytes).To(Equal([]byte("listen:start")))

			game.UpdateButtonState(false, "listen", "stop")
			Expect(mockUDPClient.NumCalledWrite).To(Equal(2))
			Expect(mockUDPClient.CalledWriteWithBytes).To(Equal([]byte("listen:stop")))
		})

		It("sends commands when the camera mount buttons are pressed", func() {
			game.UpdateButtonState(true, "camera", "left")
			Expect(mockUDPClient.NumCalledWrite).To(Equal(1))
			Expect(mockUDPClient.CalledWriteWithBytes).To(Equal([]byte("camera:left")))

			game.UpdateButtonState(false, "camera", "left")
			Expect(mockUDPClient.NumCalledWrite).To(Equal(2))
			Expect(mockUDPClient.CalledWriteWithBytes).To(Equal([]byte("camera:stop")))

			game.UpdateButtonState(true, "camera", "right")
			Expect(mockUDPClient.NumCalledWrite).To(Equal(3))

			game.UpdateButtonState(false, "camera", "right")
			Expect(mockUDPClient.NumCalledWrite).To(Equal(4))
			Expect(mockUDPClient.CalledWriteWithBytes).To(Equal([]byte("camera:stop")))
		})

	})

	Context("Robot arm", func() {

		It("sends commands when the arm buttons are pressed", func() {
			commands := []string{
				"rotate:right",
				"rotate:left",
				"shoulder:up",
				"shoulder:down",
				"elbow:bend",
				"elbow:extend",
				"wrist_pitch:up",
				"wrist_pitch:down",
				"wrist_roll:clockwise",
				"wrist_roll:counterclockwise",
				"gripper:open",
				"gripper:close",
			}

			for i, command := range commands {
				game.UpdateButtonState(true, "arm", command)
				Expect(mockUDPClient.NumCalledWrite).To(Equal(i + 1))
				Expect(mockUDPClient.CalledWriteWithBytes).To(Equal([]byte(fmt.Sprintf("arm:%s", command))))
			}
		})

	})

	Context("Reading sensor data", func() {

		It("can return an error if unable to read", func() {
			mockUDPClient.ReadError = errors.New("read error")
			Expect(game.ReadSensorData()).To(MatchError("read error"))
		})

		It("can return an error if unable to decode sensor data", func() {
			mockUDPClient.ReadReturnsBytes = []byte("not json")
			Expect(game.ReadSensorData()).To(MatchError("invalid character 'o' in literal null (expecting 'u')"))
		})

		It("can read sensor data", func() {
			data := controller.SensorData{
				Visual:           "cicada",
				Temperature:      23.0,
				TemperatureUnits: "°F",
				Humidity:         45.0,
				HumidityUnits:    "%",
				Latitude:         37.7749,
				LatitudeUnits:    "°",
				Longitude:        -122.4194,
				LongitudeUnits:   "°",
				Distance:         0.2,
				DistanceUnits:    "m",
			}
			mockUDPClient.ReadReturnsBytes, _ = json.Marshal(data)

			Expect(game.ReadSensorData()).To(Succeed())

			Expect(mockUDPClient.NumCalledRead).To(Equal(1))
			Expect(game.SensorData).NotTo(BeNil())
			Expect(game.SensorData.Visual).To(Equal("cicada"))
			Expect(game.SensorData.Temperature).To(Equal(23.0))
			Expect(game.SensorData.TemperatureUnits).To(Equal("°F"))
			Expect(game.SensorData.Humidity).To(Equal(45.0))
			Expect(game.SensorData.HumidityUnits).To(Equal("%"))
			Expect(game.SensorData.Latitude).To(Equal(37.7749))
			Expect(game.SensorData.LatitudeUnits).To(Equal("°"))
			Expect(game.SensorData.Longitude).To(Equal(-122.4194))
			Expect(game.SensorData.LongitudeUnits).To(Equal("°"))
			Expect(game.SensorData.Distance).To(Equal(0.2))
			Expect(game.SensorData.DistanceUnits).To(Equal("m"))
		})

	})

	Context("streaming sensor data", func() {

		It("can abort if the start stream command fails", func() {
			mockUDPClient.WriteError = errors.New("write error")
			ctx, _ := context.WithCancel(context.Background())

			go game.StreamSensorData(ctx)

			time.Sleep(10 * time.Millisecond)
			Expect(mockUDPClient.NumCalledWrite).To(Equal(1))
			Expect(mockUDPClient.NumCalledRead).To(BeZero())
		})

		It("can continue is the read fails with a timeout", func() {
			mockUDPClient.ReadError = os.ErrDeadlineExceeded
			ctx, _ := context.WithCancel(context.Background())

			go game.StreamSensorData(ctx)

			time.Sleep(10 * time.Millisecond)
			Expect(mockUDPClient.NumCalledRead).To(BeNumerically(">", 1))
		})

		It("can stream sensor data", func() {
			ctx, cancel := context.WithCancel(context.Background())
			data := controller.SensorData{
				Distance:      0.2,
				DistanceUnits: "m",
			}
			mockUDPClient.ReadReturnsBytes, _ = json.Marshal(data)

			go game.StreamSensorData(ctx)

			time.Sleep(10 * time.Millisecond)
			Expect(game.IsStreaming()).To(BeTrue())
			Expect(mockUDPClient.NumCalledWrite).To(Equal(1))
			Expect(mockUDPClient.CalledWriteWithBytes).To(Equal([]byte("sensor:start")))
			Expect(mockUDPClient.NumCalledRead).To(BeNumerically(">=", 1))
			cancel()
			time.Sleep(10 * time.Millisecond)
			Expect(game.IsStreaming()).To(BeFalse())
		})

	})

})
