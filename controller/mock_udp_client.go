package controller

import (
	"net"
	"time"
)

type MockUDPClient struct {
	NumCalledRead    int
	ReadReturnsBytes []byte
	ReadError        error

	NumCalledWrite       int
	CalledWriteWithBytes []byte
	WriteError           error
}

func (g *MockUDPClient) Reset() {
	g.NumCalledRead = 0
	g.ReadReturnsBytes = nil
	g.ReadError = nil

	g.NumCalledWrite = 0
	g.WriteError = nil
	g.CalledWriteWithBytes = nil
}

func (g *MockUDPClient) Read(b []byte) (n int, err error) {
	g.NumCalledRead++

	if g.ReadError != nil {
		return 0, g.ReadError
	}

	copy(b, g.ReadReturnsBytes)

	return len(g.ReadReturnsBytes), nil
}

func (g *MockUDPClient) Write(b []byte) (n int, err error) {
	g.NumCalledWrite++
	g.CalledWriteWithBytes = b

	if g.WriteError != nil {
		return 0, g.WriteError
	}

	return 0, nil
}

func (g *MockUDPClient) Close() error {
	return nil
}

func (g *MockUDPClient) LocalAddr() net.Addr {
	return nil
}

func (g *MockUDPClient) RemoteAddr() net.Addr {
	return nil
}

func (g *MockUDPClient) SetDeadline(t time.Time) error {
	return nil
}

func (g *MockUDPClient) SetReadDeadline(t time.Time) error {
	return nil
}

func (g *MockUDPClient) SetWriteDeadline(t time.Time) error {
	return nil
}
