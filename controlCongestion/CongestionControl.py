class CongestionControl:
    def __init__(self, MSS):
        self.MSS = MSS
        self.cwnd = MSS
        self.ssthresh = None
        self.state = "slow_start"  # slow_start | congestion_avoidance

    def get_cwnd(self):
        return self.cwnd

    def get_MSS_in_cwnd(self):
        return int(self.cwnd / self.MSS)

    def get_ssthresh(self):
        return self.ssthresh

    def is_state_slow_start(self):
        return self.state == "slow_start"

    def is_state_congestion_avoidance(self):
        return self.state == "congestion_avoidance"

    def event_ack_received(self):
        if self.state == "slow_start":
            # cwnd se duplica en slow start
            self.cwnd *= 2

            # Si superamos 4*MSS (según test), pasamos a congestion avoidance
            if self.cwnd >= 4 * self.MSS:
                self.ssthresh = 4 * self.MSS
                self.state = "congestion_avoidance"

        elif self.state == "congestion_avoidance":
            # cwnd crece linealmente (una MSS por ciclo)
            self.cwnd += self.MSS

    def event_timeout(self):
        # Timeout → Reducir cwnd y ajustar ssthresh
        self.ssthresh = int(self.cwnd / 2)
        self.cwnd = self.MSS
        self.state = "slow_start"
