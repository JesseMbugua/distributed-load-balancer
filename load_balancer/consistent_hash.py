import math

class ConsistentHashMap:
    def __init__(self, num_slots=512, k_virtual=9):
        self.num_slots = num_slots
        self.k_virtual = k_virtual
        self.slots = [None] * self.num_slots  # Circular ring holding server hostnames
        self.server_slots = {}  # hostname -> list of mapped slot indices

    def _hash_virtual_server(self, i: int, j: int) -> int:
        # Phi(i, j) = (i^2 + j^2 + 2j + 25) mod num_slots
        return (i**2 + j**2 + 2 * j + 25) % self.num_slots

    def _hash_request(self, req_id: int) -> int:
        # H(i) = (i^2 + 2i + 17) mod num_slots
        return (req_id**2 + 2 * req_id + 17) % self.num_slots

    def _get_server_id_int(self, hostname: str) -> int:
        # Extract digits from hostname if available, else sum char ascii values
        digits = ''.join([c for c in hostname if c.isdigit()])
        if digits:
            return int(digits)
        return sum(ord(c) for c in hostname)

    def add_server(self, hostname: str) -> bool:
        if hostname in self.server_slots:
            return False

        server_id = self._get_server_id_int(hostname)
        assigned_slots = []

        for j in range(self.k_virtual):
            base_slot = self._hash_virtual_server(server_id, j)
            slot = base_slot
            # Linear probing on collision
            while self.slots[slot] is not None:
                slot = (slot + 1) % self.num_slots

            self.slots[slot] = hostname
            assigned_slots.append(slot)

        self.server_slots[hostname] = assigned_slots
        return True

    def remove_server(self, hostname: str) -> bool:
        if hostname not in self.server_slots:
            return False

        for slot in self.server_slots[hostname]:
            self.slots[slot] = None

        del self.server_slots[hostname]
        return True

    def get_server(self, req_id: int):
        if not self.server_slots:
            return None

        start_slot = self._hash_request(req_id)
        # Search clockwise from the start slot
        for offset in range(self.num_slots):
            current_slot = (start_slot + offset) % self.num_slots
            if self.slots[current_slot] is not None:
                return self.slots[current_slot]

        return None

    def get_all_servers(self):
        return list(self.server_slots.keys())