package scenario

import (
	"fmt"
	"math"
	"strings"
)

type Mode string

const (
	ModeAuto           Mode = "auto"
	ModeBaseline       Mode = "baseline"
	ModeStragglerBurst Mode = "straggler-burst"
)

type Engine struct {
	Seed int64
}

func New(seed int64) Engine {
	return Engine{Seed: seed}
}

func ParseMode(raw string) (Mode, error) {
	switch Mode(strings.ToLower(strings.TrimSpace(raw))) {
	case ModeAuto, ModeBaseline, ModeStragglerBurst:
		return Mode(strings.ToLower(strings.TrimSpace(raw))), nil
	default:
		return "", fmt.Errorf("unsupported scenario mode %q", raw)
	}
}

func (e Engine) Name(step int64) string {
	return e.NameWithControl(step, ModeAuto, 0)
}

func (e Engine) NameWithControl(step int64, mode Mode, untilStep int64) string {
	if mode != ModeAuto {
		if untilStep == 0 || step <= untilStep {
			return string(mode)
		}
	}
	if e.burstActive(step) {
		return string(ModeStragglerBurst)
	}
	return string(ModeBaseline)
}

func (e Engine) DriftMultiplier(step int64, host int, gpu int) float64 {
	if e.Name(step) != string(ModeStragglerBurst) {
		return 1 + e.noise(step, host, gpu)*0.12
	}
	if e.inBurstCohort(host, gpu) {
		return 4.0 + e.noise(step, host, gpu)*0.5
	}
	if e.nearBurstHost(host) {
		return 1.25 + e.noise(step, host, gpu)*0.2
	}
	return 1.08 + e.noise(step, host, gpu)*0.1
}

func (e Engine) PacketLoss(step int64, host int, gpu int) float64 {
	if e.Name(step) == string(ModeStragglerBurst) && host == 12 && gpu >= 4 && gpu <= 6 {
		return 0.65 + e.noise(step, host, gpu)*0.05
	}
	base := 0.012 + math.Mod(float64(host+gpu), 4)*0.008
	if e.nearBurstHost(host) {
		base += 0.03
	}
	return math.Max(0.0, base+e.noise(step, host, gpu)*0.004)
}

func (e Engine) ClockDrift(step int64, host int, gpu int) float64 {
	base := math.Sin(float64(step+int64(host))/9.0)*42 + math.Cos(float64(step+int64(gpu))/7.0)*14
	base += float64((host%5)-2) * 5.5
	if e.Name(step) == string(ModeStragglerBurst) && e.inBurstCohort(host, gpu) {
		base *= 4
	} else if e.nearBurstHost(host) {
		base *= 1.35
	}
	return base
}

func (e Engine) burstActive(step int64) bool {
	cycle := int64(96)
	windowStart := int64(28)
	windowEnd := int64(44)
	offset := e.Seed % 11
	phase := (step + offset) % cycle
	return phase >= windowStart && phase <= windowEnd
}

func (e Engine) inBurstCohort(host int, gpu int) bool {
	seedBias := int((e.Seed % 7) + 3)
	return host == 12 && gpu >= 4 && gpu <= 6 || host == 11 && gpu == seedBias%8 || host == 13 && gpu == (seedBias+2)%8
}

func (e Engine) nearBurstHost(host int) bool {
	return host >= 10 && host <= 14
}

func (e Engine) noise(step int64, host int, gpu int) float64 {
	value := float64((step+int64(host*31)+int64(gpu*17)+e.Seed*13)%1000) / 1000.0
	return (value - 0.5) * 2
}
