class CongestionControl:
    def __init__(self, MSS):
        self.MSS = MSS
        self.cwnd = MSS
        self.ssthresh = None
        self.state = "slow_start"
        self.acks_in_round = 0  # contador de ACKs en la ronda actual

    # --- Getters ---
    def get_cwnd(self):
        return self.cwnd

    def get_MSS_in_cwnd(self):
        return self.cwnd // self.MSS

    def get_ssthresh(self):
        return self.ssthresh

    def is_state_slow_start(self):
        return self.state == "slow_start"

    def is_state_congestion_avoidance(self):
        return self.state == "congestion_avoidance"

    # --- Eventos ---
    def event_ack_received(self):
        if self.state == "slow_start":
            # crecimiento exponencial
            self.cwnd += self.MSS
            # pasar a congestion avoidance si llegamos a ssthresh
            if self.ssthresh is not None and self.cwnd >= self.ssthresh:
                self.state = "congestion_avoidance"
        elif self.state == "congestion_avoidance":
            # crecimiento lineal: +1 MSS por ronda
            self.acks_in_round += 1
            if self.acks_in_round >= self.get_MSS_in_cwnd():
                self.cwnd += self.MSS
                self.acks_in_round = 0

    def event_timeout(self):
        # calcular nuevo ssthresh como mitad de cwnd actual
        self.ssthresh = int(self.cwnd / 2)
        if self.ssthresh < self.MSS:
            self.ssthresh = self.MSS
        # reiniciar
        self.cwnd = self.MSS
        self.state = "slow_start"
        self.acks_in_round = 0
