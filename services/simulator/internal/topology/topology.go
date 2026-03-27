package topology

import (
	"fmt"

	"github.com/stan/clockwork_fullstack/services/simulator/internal/contracts"
)

const (
	HostCount      = 32
	GPUsPerHost    = 8
	TotalNodeCount = HostCount * GPUsPerHost
	hostsPerRack   = 4
)

func NodeID(host, gpu int) string {
	return fmt.Sprintf("gpu-%02d-%02d", host, gpu)
}

func HostID(host int) string {
	return fmt.Sprintf("host-%02d", host)
}

func RackForHost(host int) int {
	return host / hostsPerRack
}

func Build() contracts.TopologyResponse {
	nodes := make([]contracts.TopologyNode, 0, TotalNodeCount)
	links := make([]contracts.TopologyLink, 0, 3000)

	for host := 0; host < HostCount; host++ {
		hostID := HostID(host)
		for gpu := 0; gpu < GPUsPerHost; gpu++ {
			nodes = append(nodes, contracts.TopologyNode{
				ID:     NodeID(host, gpu),
				HostID: hostID,
				Group:  host,
			})
		}
	}

	// Dense intra-host fabric approximates NVLink.
	for host := 0; host < HostCount; host++ {
		for left := 0; left < GPUsPerHost; left++ {
			for right := left + 1; right < GPUsPerHost; right++ {
				links = append(links, contracts.TopologyLink{
					Source: NodeID(host, left),
					Target: NodeID(host, right),
					Kind:   "nvlink",
				})
			}
		}
	}

	// Multi-hop RoCE uplinks create visible fabric structure across racks.
	for rack := 0; rack < HostCount/hostsPerRack; rack++ {
		startHost := rack * hostsPerRack
		endHost := startHost + hostsPerRack
		for host := startHost; host < endHost; host++ {
			for peer := startHost; peer < endHost; peer++ {
				if host == peer {
					continue
				}
				links = append(links, contracts.TopologyLink{
					Source: NodeID(host, 0),
					Target: NodeID(peer, 0),
					Kind:   "roce",
				})
			}
		}
		if rack < (HostCount/hostsPerRack)-1 {
			links = append(links, contracts.TopologyLink{
				Source: NodeID(startHost, 0),
				Target: NodeID(endHost, 0),
				Kind:   "roce",
			})
		}
	}

	return contracts.TopologyResponse{
		Nodes: nodes,
		Links: links,
	}
}
