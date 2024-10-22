import random
from typing import List


class Client:
    def __init__(self):
        self.amount = random.choices(
            ["little", "medium", "many"], weights=[20, 60, 20], k=1
        )[0]
        self.time_in_queue = 0

    def __repr__(self):
        return f"Amount: {self.amount}; Time in queue = {self.time_in_queue}"


class SSCheckout:
    def __init__(self):
        self.free_at = 0

    def __repr__(self):
        return f"Free at: {self.free_at}"

    def process_client(self, client: Client):
        if client.amount == "little":
            self.free_at += random.randint(1, 3)
        elif client.amount == "medium":
            self.free_at += random.randint(4, 7)
        elif client.amount == "many":
            self.free_at += random.randint(7, 10)
        return client


class Kolejka:
    def __init__(self):
        self.queue: list[Client] = []

    def is_empty(self):
        return True if len(self.queue) == 0 else False

    def add_client(self, client: Client):
        self.queue.append(client)

    def will_client_leave(self):
        if random.uniform(0, 1) > 0.95:
            self.queue.pop(random.randint(0, len(self.queue)))

    def increase_clients_in_queue_time(self):
        for client in self.queue:
            client.time_in_queue += 1


def symulacja(kolejka: Kolejka, kasy: List[SSCheckout]):
    prawdopodobienstwo_klienta = 0.95
    processed_clients_times: list[int] = []
    for timer in range(600):
        if random.uniform(0, 1) > 1 - prawdopodobienstwo_klienta:
            klient = Client()
            kolejka.add_client(klient)

        for kasa in kasy:
            if timer >= kasa.free_at and not kolejka.is_empty():
                processed_client = kasa.process_client(client=kolejka.queue.pop(0))
                processed_clients_times.append(processed_client.time_in_queue)

        kolejka.increase_clients_in_queue_time()

        print(f"{timer}. długość kolejki = {len(kolejka.queue)}")
    print(
        f"Średni czas klienta w kolejce = {round(sum(processed_clients_times) / len(processed_clients_times), 2)}"
    )


def main():
    kolejka = Kolejka()  # kolejka
    kasy = [SSCheckout() for _ in range(5)]  # kanały obsługi
    #  przerwa - mniej klientów niż kas więc jakieś nie pracują
    symulacja(kolejka=kolejka, kasy=kasy)


if __name__ == "__main__":
    main()
