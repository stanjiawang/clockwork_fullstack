package contracts

type RawNodeMetric struct {
	NodeID        string  `json:"node_id"`
	HostID        string  `json:"host_id"`
	ClockOffsetNS float64 `json:"clock_offset_ns"`
	P2PLatencyUS  float64 `json:"p2p_latency_us"`
	PacketLossPct float64 `json:"packet_loss_pct"`
	TimestampMS   int64   `json:"timestamp_ms"`
}

type TopologyNode struct {
	ID     string `json:"id"`
	HostID string `json:"host_id"`
	Group  int    `json:"group"`
}

type TopologyLink struct {
	Source string `json:"source"`
	Target string `json:"target"`
	Kind   string `json:"kind"`
}

type TopologyResponse struct {
	Nodes []TopologyNode `json:"nodes"`
	Links []TopologyLink `json:"links"`
}

type ScenarioResponse struct {
	Name string `json:"name"`
	Seed int64  `json:"seed"`
}
