import random
from typing import List


class Client:
    def __init__(self):
        self.amount = random.choice(["little", "medium", "many"])


class SSCheckout:
    def __init__(self):
        self.free_at = 0

    def process_client(self, client: Client):
        if client.amount == "little":
            self.free_at += random.randint(1, 3)
        elif client.amount == "medium":
            self.free_at += random.randint(4, 7)
        elif client.amount == "many":
            self.free_at += random.randint(7, 10)


class Kolejka:
    def __init__(self):
        self.queue = []

    def is_empty(self):
        return True if len(self.queue) == 0 else False

    def add_client(self, client: Client):
        self.queue.append(client)

    def will_client_leave(self):
        if random.uniform(0, 1) > 0.95:
            self.queue.pop(random.randint(0, len(self.queue)))


def symulacja(kolejka: Kolejka, kasy: List[SSCheckout]):
    prawdopodobienstwo_klienta = 0.95
    for timer in range(600):
        if random.uniform(0, 1) > 1 - prawdopodobienstwo_klienta:
            klient = Client()
            kolejka.add_client(klient)

        for kasa in kasy:
            if timer >= kasa.free_at and not kolejka.is_empty():
                kasa.process_client(client=kolejka.queue.pop(0))

        print(f"{timer}. długość kolejki = {len(kolejka.queue)}")


def main():
    kolejka = Kolejka()  # kolejka
    kasy = [SSCheckout() for _ in range(5)]  # kanały obsługi
    #  przerwa - mniej klientów niż kas więc jakieś nie pracują
    symulacja(kolejka=kolejka, kasy=kasy)


if __name__ == "__main__":
    main()
