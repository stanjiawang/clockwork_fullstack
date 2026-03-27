package topology

import "testing"

func TestBuildReturnsExpectedCounts(t *testing.T) {
	topo := Build()

	if got := len(topo.Nodes); got != TotalNodeCount {
		t.Fatalf("expected %d nodes, got %d", TotalNodeCount, got)
	}

	if got := len(topo.Links); got < 900 {
		t.Fatalf("expected rich link set, got %d links", got)
	}

	if topo.Nodes[0].ID != "gpu-00-00" {
		t.Fatalf("unexpected first node id: %s", topo.Nodes[0].ID)
	}
	if topo.Nodes[len(topo.Nodes)-1].HostID != "host-31" {
		t.Fatalf("unexpected last host id: %s", topo.Nodes[len(topo.Nodes)-1].HostID)
	}
}
