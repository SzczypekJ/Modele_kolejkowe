import random
import numpy as np
import matplotlib.pyplot as plt
from typing import List


class Client:
    def __init__(self, arrival_time):
        self.amount = random.choices(
            ["little", "medium", "many"], weights=[20, 60, 20], k=1
        )[0]
        self.time_in_queue = 0
        self.arrival_time = arrival_time
        # self.patience = random.randint(5, 15)  # Maksymalny czas oczekiwania
        self.patience = 2

    def __repr__(self):
        return f"Amount: {self.amount}; Time in queue = {self.time_in_queue}"


class SSCheckout:
    def __init__(self):
        self.free_at = 0
        self.busy_time = 0  # Czas, kiedy kasa jest zajęta
        self.clients_served = 0  # Liczba obsłużonych klientów

    def __repr__(self):
        return f"Free at: {self.free_at}"

    def process_client(self, client: Client, current_time):
        client_time = 0
        if client.amount == "little":
            # client_time = random.randint(1, 3)
            client_time = 2
        elif client.amount == "medium":
            # client_time = random.randint(4, 7)
            client_time = 4
        elif client.amount == "many":
            # client_time = random.randint(8, 10)
            client_time = 6
        self.free_at = current_time + client_time
        self.clients_served += 1  # Zwiększ licznik obsłużonych klientów przez tę kasę
        return client_time


class Kolejka:
    def __init__(self):
        self.queue: List[Client] = []
        self.num_impatient_clients = 0  # Licznik niecierpliwych klientów

    def is_empty(self):
        return len(self.queue) == 0

    def add_client(self, client: Client):
        self.queue.append(client)

    def remove_impatient_clients(self):
        remaining_clients = []
        for client in self.queue:
            if client.time_in_queue < client.patience:
                # Klient jest cierpliwy, pozostaje w kolejce
                remaining_clients.append(client)
            else:
                # Klient jest niecierpliwy
                # if random.uniform(0, 1) > 0.5:
                #     # Klient decyduje się opuścić kolejkę
                #     self.num_impatient_clients += 1  # Zwiększ licznik
                #     # Nie dodajemy klienta do remaining_clients
                # else:
                #     # Klient decyduje się pozostać w kolejce
                #     remaining_clients.append(client)
                self.num_impatient_clients += 1
        self.queue = remaining_clients

    def increase_clients_in_queue_time(self):
        for client in self.queue:
            client.time_in_queue += 1


def symulacja(
    kolejka: Kolejka,
    kasy: List[SSCheckout],
    czas_trwania: int,
    srednia_intensywnosc_przyjsc: float,
):
    # Inicjalizacja zmiennych
    processed_clients_times: List[int] = []
    queue_lengths: List[int] = []
    waiting_times: List[int] = []
    clients_served_per_time = [0] * czas_trwania
    cumulative_waiting_time = []
    total_clients_served = 0

    # Generowanie czasów przyjścia klientów
    arrival_times = []
    next_arrival = np.random.exponential(1 / srednia_intensywnosc_przyjsc)
    while next_arrival < czas_trwania:
        arrival_times.append(int(next_arrival))
        next_arrival += np.random.exponential(1 / srednia_intensywnosc_przyjsc)

    total_clients_arrived = len(arrival_times)

    # Główna pętla symulacji
    current_arrival_index = 0
    for timer in range(czas_trwania):
        # Przybycie klienta
        while (
            current_arrival_index < len(arrival_times)
            and timer == arrival_times[current_arrival_index]
        ):
            klient = Client(arrival_time=timer)
            kolejka.add_client(klient)
            current_arrival_index += 1

        # Obsługa klientów w kasach
        free_cashiers = [i for i, kasa in enumerate(kasy) if kasa.free_at <= timer]
        while free_cashiers and not kolejka.is_empty():
            # Losowo wybieramy indeks wolnej kasy
            i = random.choice(free_cashiers)
            kasa = kasy[i]

            # Obsługujemy klienta
            client = kolejka.queue.pop(0)
            client_wait_time = timer - client.arrival_time
            processing_time = kasa.process_client(client, timer)
            total_time_in_system = client_wait_time + processing_time
            processed_clients_times.append(total_time_in_system)
            waiting_times.append(client_wait_time)
            clients_served_per_time[timer] += (
                1  # Zwiększ licznik obsłużonych klientów w tym momencie czasu
            )
            total_clients_served += 1  # Zwiększ całkowity licznik obsłużonych klientów

            # Aktualizujemy listę wolnych kas
            free_cashiers.remove(i)

        cumulative_waiting_time.append(
            sum(waiting_times) / total_clients_served if total_clients_served > 0 else 0
        )
        # Aktualizacja czasu zajętości kas
        for kasa in kasy:
            if kasa.free_at > timer:
                kasa.busy_time += 1

        # Aktualizacja czasu oczekiwania klientów w kolejce
        kolejka.increase_clients_in_queue_time()
        kolejka.remove_impatient_clients()

        # Zbieranie danych do wykresów
        queue_lengths.append(len(kolejka.queue))

    # Obliczenia statystyk
    if processed_clients_times:
        sredni_czas_w_systemie = round(
            sum(processed_clients_times) / len(processed_clients_times), 2
        )
        sredni_czas_oczekiwania = round(sum(waiting_times) / len(waiting_times), 2)
    else:
        sredni_czas_w_systemie = 0
        sredni_czas_oczekiwania = 0
    wykorzystanie_kas = [
        round((kasa.busy_time / czas_trwania) * 100, 2) for kasa in kasy
    ]

    clients_remaining_in_queue = len(kolejka.queue)

    # Wyświetlenie wyników
    print(
        f"Całkowita liczba klientów, którzy przyszli do systemu: {total_clients_arrived}"
    )
    print(f"Liczba obsłużonych klientów: {total_clients_served}")
    print(
        f"Liczba klientów, którzy opuścili kolejkę z powodu braku cierpliwości: {kolejka.num_impatient_clients}"
    )
    print(
        f"Liczba klientów pozostałych w kolejce po zakończeniu symulacji: {clients_remaining_in_queue}"
    )
    print(f"Średni czas klienta w systemie = {sredni_czas_w_systemie}")
    print(f"Średni czas oczekiwania w kolejce = {sredni_czas_oczekiwania}")
    for i, wykorzystanie in enumerate(wykorzystanie_kas):
        print(
            f"Kasa {i + 1} była zajęta przez {wykorzystanie}% czasu i obsłużyła {kasy[i].clients_served} klientów."
        )

    # Generowanie wykresów
    # Wykres długości kolejki w czasie
    plt.figure(figsize=(12, 6))
    plt.plot(range(czas_trwania), queue_lengths, label="Długość kolejki")
    avg_queue_length = np.mean(queue_lengths)
    plt.axhline(
        y=avg_queue_length, color="red", linestyle="--", label="Średnia długość kolejki"
    )
    plt.title("Długość kolejki w czasie")
    plt.xlabel("Czas")
    plt.ylabel("Liczba klientów w kolejce")
    plt.legend()
    plt.grid(True)
    plt.savefig("queue_length_over_time.png")
    plt.close()

    # Histogram czasu spędzonego w systemie przez klientów
    plt.figure(figsize=(8, 6))
    plt.hist(
        processed_clients_times, bins=20, edgecolor="black", label="Czas w systemie"
    )
    plt.xlim(0, max(processed_clients_times) + 1)
    plt.axvline(
        x=sredni_czas_w_systemie,
        color="red",
        linestyle="--",
        label="Średni czas w systemie",
    )
    plt.title("Rozkład czasu spędzonego w systemie przez klientów")
    plt.xlabel("Czas (jednostki czasu)")
    plt.ylabel("Liczba klientów")
    plt.legend()
    plt.grid(True)
    plt.savefig("time_in_system_distribution.png")
    plt.close()

    # Histogram czasu oczekiwania w kolejce
    plt.figure(figsize=(8, 6))
    plt.hist(
        waiting_times, bins=20, edgecolor="black", label="Czas oczekiwania w kolejce"
    )
    plt.axvline(
        x=sredni_czas_oczekiwania,
        color="red",
        linestyle="--",
        label="Średni czas oczekiwania",
    )
    plt.title("Rozkład czasu oczekiwania w kolejce")
    plt.xlabel("Czas oczekiwania (jednostki czasu)")
    plt.ylabel("Liczba klientów")
    plt.legend()
    plt.grid(True)
    plt.savefig("waiting_time_distribution.png")
    plt.close()

    # Wykres liczby obsłużonych klientów w czasie
    plt.figure(figsize=(12, 6))
    plt.plot(range(czas_trwania), clients_served_per_time, label="Obsłużeni klienci")
    plt.title("Liczba obsłużonych klientów w czasie")
    plt.xlabel("Czas")
    plt.ylabel("Liczba obsłużonych klientów")
    plt.legend()
    plt.grid(True)
    plt.savefig("clients_served_over_time.png")
    plt.close()

    # Wykres średniego czasu oczekiwania w czasie
    plt.figure(figsize=(12, 6))
    plt.plot(
        range(len(cumulative_waiting_time)),
        cumulative_waiting_time,
        label="Średni czas oczekiwania",
    )
    plt.title("Średni czas oczekiwania w czasie")
    plt.xlabel("Czas")
    plt.ylabel("Średni czas oczekiwania (jednostki czasu)")
    plt.legend()
    plt.grid(True)
    plt.savefig("average_waiting_time_over_time.png")
    plt.close()

    # Wykres wykorzystania kas
    plt.figure(figsize=(8, 6))
    plt.bar(range(1, len(kasy) + 1), wykorzystanie_kas)
    plt.title("Wykorzystanie kas")
    plt.xlabel("Numer kasy")
    plt.ylabel("Procent czasu zajętości")
    plt.grid(True)
    plt.savefig("cashier_utilization.png")
    plt.close()

    # Wykres liczby klientów obsłużonych przez każdą kasę
    clients_served_by_cashier = [kasa.clients_served for kasa in kasy]
    plt.figure(figsize=(8, 6))
    plt.bar(range(1, len(kasy) + 1), clients_served_by_cashier)
    plt.title("Liczba klientów obsłużonych przez każdą kasę")
    plt.xlabel("Numer kasy")
    plt.ylabel("Liczba obsłużonych klientów")
    plt.grid(True)
    plt.savefig("clients_served_by_cashier.png")
    plt.close()


def main():
    kolejka = Kolejka()

    # Pobieranie parametrów od użytkownika
    liczba_kas = int(input("Podaj liczbę kas: "))
    czas_trwania = int(input("Podaj czas trwania symulacji: "))
    srednia_intensywnosc_przyjsc = float(
        input("Podaj średnią intensywność przyjść klientów na jednostkę czasu: ")
    )

    kasy = [SSCheckout() for _ in range(liczba_kas)]
    symulacja(
        kolejka=kolejka,
        kasy=kasy,
        czas_trwania=czas_trwania,
        srednia_intensywnosc_przyjsc=srednia_intensywnosc_przyjsc,
    )


if __name__ == "__main__":
    main()
