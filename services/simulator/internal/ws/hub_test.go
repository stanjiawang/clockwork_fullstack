package ws

import (
	"strings"
	"testing"
)

func TestHubBroadcastQueuesPayloadForClient(t *testing.T) {
	hub := NewHub()
	testClient := &client{
		send: make(chan []byte, 1),
	}
	hub.clients[testClient] = struct{}{}

	hub.Broadcast(map[string]string{"status": "ok"})

	select {
	case payload := <-testClient.send:
		if !strings.Contains(string(payload), `"status":"ok"`) {
			t.Fatalf("unexpected payload: %s", string(payload))
		}
	default:
		t.Fatal("expected payload to be queued for client")
	}
}

func TestHubCloseMarksHubClosed(t *testing.T) {
	hub := NewHub()

	hub.Close()

	if !hub.closed {
		t.Fatal("expected hub to be marked closed")
	}
	if hub.Count() != 0 {
		t.Fatalf("expected no clients after close, got %d", hub.Count())
	}
}

func BenchmarkHubBroadcast(b *testing.B) {
	hub := NewHub()
	testClient := &client{
		send: make(chan []byte, 1),
	}
	hub.clients[testClient] = struct{}{}
	defer hub.Close()

	payload := map[string]string{"status": "ok"}
	b.ReportAllocs()
	for i := 0; i < b.N; i++ {
		hub.Broadcast(payload)
		select {
		case <-testClient.send:
		default:
		}
	}
}
