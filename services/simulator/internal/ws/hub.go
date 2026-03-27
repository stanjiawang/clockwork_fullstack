package ws

import (
	"encoding/json"
	"errors"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

const (
	readLimitBytes  = 1 << 20
	readTimeout     = 30 * time.Second
	writeTimeout    = 5 * time.Second
	pingInterval    = 15 * time.Second
	clientQueueSize = 8
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true
	},
}

type Hub struct {
	mu             sync.Mutex
	clients        map[*client]struct{}
	closed         bool
	broadcasts     uint64
	droppedClients uint64
}

type Stats struct {
	ConnectedClients int    `json:"connected_clients"`
	Broadcasts       uint64 `json:"broadcasts"`
	DroppedClients   uint64 `json:"dropped_clients"`
	Closed           bool   `json:"closed"`
}

type client struct {
	conn *websocket.Conn
	send chan []byte
	once sync.Once
}

func NewHub() *Hub {
	return &Hub{
		clients: make(map[*client]struct{}),
	}
}

func (h *Hub) Handle(w http.ResponseWriter, r *http.Request) error {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		return err
	}

	conn.SetReadLimit(readLimitBytes)
	_ = conn.SetReadDeadline(time.Now().Add(readTimeout))
	conn.SetPongHandler(func(string) error {
		return conn.SetReadDeadline(time.Now().Add(readTimeout))
	})

	c := &client{
		conn: conn,
		send: make(chan []byte, clientQueueSize),
	}

	if !h.register(c) {
		return errors.New("hub closed")
	}
	go c.writePump()
	c.readPump(h)
	return nil
}

func (h *Hub) Broadcast(payload any) {
	data, err := json.Marshal(payload)
	if err != nil {
		return
	}

	h.mu.Lock()
	if h.closed {
		h.mu.Unlock()
		return
	}
	h.broadcasts++
	var slow []*client
	for c := range h.clients {
		select {
		case c.send <- data:
		default:
			delete(h.clients, c)
			slow = append(slow, c)
		}
	}
	h.droppedClients += uint64(len(slow))
	h.mu.Unlock()

	for _, c := range slow {
		c.close()
	}
}

func (h *Hub) Count() int {
	h.mu.Lock()
	defer h.mu.Unlock()
	return len(h.clients)
}

func (h *Hub) Snapshot() Stats {
	h.mu.Lock()
	defer h.mu.Unlock()
	return Stats{
		ConnectedClients: len(h.clients),
		Broadcasts:       h.broadcasts,
		DroppedClients:   h.droppedClients,
		Closed:           h.closed,
	}
}

func (h *Hub) register(c *client) bool {
	h.mu.Lock()
	defer h.mu.Unlock()
	if h.closed {
		_ = c.conn.Close()
		return false
	}
	h.clients[c] = struct{}{}
	return true
}

func (h *Hub) unregister(c *client) {
	h.mu.Lock()
	if _, ok := h.clients[c]; !ok {
		h.mu.Unlock()
		return
	}
	delete(h.clients, c)
	h.mu.Unlock()
	c.close()
}

func (c *client) readPump(h *Hub) {
	defer h.unregister(c)
	for {
		if _, _, err := c.conn.NextReader(); err != nil {
			return
		}
	}
}

func (c *client) writePump() {
	ticker := time.NewTicker(pingInterval)
	defer ticker.Stop()
	for {
		select {
		case payload, ok := <-c.send:
			if !ok {
				return
			}
			_ = c.conn.SetWriteDeadline(time.Now().Add(writeTimeout))
			if err := c.conn.WriteMessage(websocket.TextMessage, payload); err != nil {
				return
			}
		case <-ticker.C:
			_ = c.conn.SetWriteDeadline(time.Now().Add(writeTimeout))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

func (h *Hub) Close() {
	h.mu.Lock()
	h.closed = true
	clients := make([]*client, 0, len(h.clients))
	for c := range h.clients {
		clients = append(clients, c)
	}
	h.clients = make(map[*client]struct{})
	h.mu.Unlock()

	for _, c := range clients {
		c.close()
	}
}

func (c *client) close() {
	c.once.Do(func() {
		close(c.send)
		_ = c.conn.Close()
	})
}
