import random
from typing import List, Optional, Tuple
import matplotlib.pyplot as plt


class Request:
    def __init__(self, id: int, arrival_time: int):
        self.id = id
        self.arrival_time = arrival_time
        self.time_in_system = 0
        self.type = self.assign_type()
        self.current_stage = "Magazyn Surowców"
        self.waiting_time = 0
        self.in_transit = False
        self.next_stage_arrival_time = None

    def assign_type(self) -> str:
        return random.choices(
            ["zielony", "czerwony", "niebieski"], weights=[85, 10, 5], k=1
        )[0]

    def __repr__(self):
        return (
            f"Zgłoszenie {self.id}: Typ={self.type}, Obecny etap={self.current_stage}"
        )


class Stage:
    def __init__(
        self, name: str, capacity: int | float = 0, queue_limit: Optional[int] = None
    ):
        self.name = name
        self.capacity = (
            capacity  # Maksymalna liczba zgłoszeń przetwarzanych w jednostce czasu
        )
        self.queue_limit = (
            queue_limit  # Maksymalna liczba zgłoszeń w kolejce (opcjonalnie)
        )
        self.queue: List[Request] = []
        self.transit_queue: List[
            Tuple[Request, int]
        ] = []  # Zgłoszenia w tranzycie do kolejnego etapu
        self.processed_requests: List[Request] = []
        self.next_stages = []
        self.statistics = {"zielony": 0, "czerwony": 0, "niebieski": 0}
        self.queue_lengths = []
        self.utilization = []
        self.processed_per_time = []
        self.time = []
        self.capacity_history = []
        self.total_waiting_time = 0  # Całkowity czas oczekiwania w kolejce
        self.max_queue_length = 0  # Maksymalna długość kolejki

    def add_next_stage(self, stage, condition):
        self.next_stages.append((stage, condition))

    def receive(self, requests: List[Request]):
        if self.queue_limit is not None:
            available_space = self.queue_limit - len(self.queue)
            if available_space <= 0:
                # Kolejka jest pełna, odrzucamy zgłoszenia
                return
            else:
                self.queue.extend(requests[:available_space])
        else:
            self.queue.extend(requests)

    def is_empty(self) -> bool:
        return len(self.queue) == 0

    def process(self, current_time: int):
        # Losowanie przepustowości na tę jednostkę czasu
        if self.name == "Linia Produkcyjna":
            self.capacity = random.randint(20, 80)
        elif self.name == "Personalizacja":
            self.capacity = random.randint(4, 8)
        elif self.name == "Standardowe Testy Jakości":
            self.capacity = random.randint(30, 65)
        elif self.name == "Badania na Prototypach":
            self.capacity = random.randint(1, 5)
        elif self.name == "Wysyłka":
            self.capacity = random.randint(30, 65)
        # Dla magazynu surowców przepustowość jest nieskończona i nie zmienia się

        # Zapisujemy historię przepustowości
        self.capacity_history.append(self.capacity)

        # Procesuj zgłoszenia w kolejności priorytetów: niebieskie, czerwone, zielone
        processed_this_unit = []
        blues = [r for r in self.queue if r.type == "niebieski"]
        reds = [r for r in self.queue if r.type == "czerwony"]
        greens = [r for r in self.queue if r.type == "zielony"]

        # Łączna liczba przetworzonych zgłoszeń w tej jednostce czasu
        total_processed = 0

        for requests_of_type in [blues, reds, greens]:
            for request in requests_of_type:
                if total_processed >= self.capacity:
                    break  # Osiągnięto maksymalną przepustowość
                self.process_request(request, current_time)
                processed_this_unit.append(request)
                total_processed += 1
            if total_processed >= self.capacity:
                break  # Osiągnięto maksymalną przepustowość

        # Usuń przetworzone zgłoszenia z kolejki
        for request in processed_this_unit:
            self.queue.remove(request)

        # Aktualizuj statystyki kolejki
        self.queue_lengths.append(len(self.queue))
        self.max_queue_length = max(self.max_queue_length, len(self.queue))

        # Aktualizuj statystyki wykorzystania
        utilization_percent = (
            (total_processed / self.capacity) * 100 if self.capacity > 0 else 0
        )
        self.utilization.append(utilization_percent)
        self.processed_per_time.append(total_processed)
        self.time.append(current_time)

        # Aktualizuj całkowity czas oczekiwania
        self.total_waiting_time += sum(r.waiting_time for r in self.queue)

    def process_request(self, request: Request, current_time: int):
        # Aktualizacja statystyk
        self.statistics[request.type] += 1

        # Ustaw aktualny etap zgłoszenia
        request.current_stage = self.name

        # Ustaw zgłoszenie w tranzycie
        request.in_transit = True
        request.next_stage_arrival_time = (
            current_time + 1
        )  # Przybędzie za 1 jednostkę czasu

        # Dodaj zgłoszenie do kolejki tranzytu
        self.transit_queue.append((request, current_time))

    def update_transit(self, current_time: int):
        # Sprawdź, czy jakieś zgłoszenia dotarły do kolejnego etapu
        arrived_requests = []
        for request, departure_time in self.transit_queue:
            if current_time >= request.next_stage_arrival_time:
                arrived_requests.append(request)

        # Usuń zgłoszenia, które dotarły
        self.transit_queue = [
            (r, t) for r, t in self.transit_queue if r not in arrived_requests
        ]

        # Przekieruj zgłoszenia do kolejnych etapów na podstawie warunków
        for request in arrived_requests:
            request.in_transit = False
            for next_stage, condition in self.next_stages:
                if condition(request):
                    next_stage.receive([request])
                    break  # Zgłoszenie trafia tylko do jednego etapu
            else:
                # Jeśli nie ma następnego etapu, zgłoszenie opuszcza system
                self.processed_requests.append(request)
                request.time_in_system = current_time - request.arrival_time

    def update_waiting_times(self):
        for request in self.queue:
            request.waiting_time += 1


# Definicja konkretnych etapów
class MagazynSurowcow(Stage):
    def __init__(self):
        super().__init__("Magazyn Surowców", capacity=float("inf"))


class LiniaProdukcyjna(Stage):
    def __init__(self):
        super().__init__("Linia Produkcyjna")  # Początkowa wartość nie ma znaczenia


class Personalizacja(Stage):
    def __init__(self):
        super().__init__("Personalizacja")


class TestyJakosci(Stage):
    def __init__(self):
        super().__init__("Standardowe Testy Jakości")


class BadaniaPrototypow(Stage):
    def __init__(self):
        super().__init__("Badania na Prototypach")


class Wysylka(Stage):
    def __init__(self):
        super().__init__("Wysyłka")


def symulacja(czas_trwania: int):
    # Inicjalizacja etapów
    magazyn = MagazynSurowcow()
    linia_produkcyjna = LiniaProdukcyjna()
    personalizacja = Personalizacja()
    testy_jakosci = TestyJakosci()
    badania_prototypow = BadaniaPrototypow()
    wysylka = Wysylka()

    # Definiowanie przepływu między etapami
    magazyn.add_next_stage(linia_produkcyjna, lambda r: True)

    # Linia Produkcyjna
    linia_produkcyjna.add_next_stage(
        testy_jakosci, lambda r: r.type == "zielony" and random.uniform(0, 1) < 0.99
    )
    linia_produkcyjna.add_next_stage(
        personalizacja, lambda r: r.type == "czerwony" and random.uniform(0, 1) < 0.99
    )
    linia_produkcyjna.add_next_stage(
        badania_prototypow,
        lambda r: r.type == "niebieski" or random.uniform(0, 1) >= 0.99,
    )

    # Personalizacja
    personalizacja.add_next_stage(testy_jakosci, lambda r: random.uniform(0, 1) < 0.99)
    personalizacja.add_next_stage(
        badania_prototypow, lambda r: random.uniform(0, 1) >= 0.99
    )

    # Testy Jakości
    testy_jakosci.add_next_stage(wysylka, lambda r: random.uniform(0, 1) < 0.99)
    testy_jakosci.add_next_stage(
        badania_prototypow, lambda r: random.uniform(0, 1) >= 0.99
    )

    # Wszystkie zgłoszenia
    wszystkie_zgloszenia = []

    # Główna pętla symulacji
    current_time = 0
    while current_time < czas_trwania:
        # Generuj losową liczbę zgłoszeń od 20 do 80
        num_new_requests = random.randint(20, 80)
        new_requests = [
            Request(id=len(wszystkie_zgloszenia) + i + 1, arrival_time=current_time)
            for i in range(num_new_requests)
        ]
        wszystkie_zgloszenia.extend(new_requests)

        # Dodaj nowe zgłoszenia do magazynu
        magazyn.receive(new_requests)

        # Procesuj każdy etap
        for stage in [
            magazyn,
            linia_produkcyjna,
            personalizacja,
            testy_jakosci,
            badania_prototypow,
            wysylka,
        ]:
            stage.process(current_time)
            stage.update_waiting_times()

        # Aktualizuj tranzyty między etapami
        for stage in [
            magazyn,
            linia_produkcyjna,
            personalizacja,
            testy_jakosci,
            badania_prototypow,
        ]:
            stage.update_transit(current_time)

        current_time += 1

    # Zbieranie statystyk
    wszystkie_etapy = [
        magazyn,
        linia_produkcyjna,
        personalizacja,
        testy_jakosci,
        badania_prototypow,
        wysylka,
    ]
    total_exits = len(badania_prototypow.processed_requests) + len(
        wysylka.processed_requests
    )
    total_time_in_system = sum(
        r.time_in_system
        for r in badania_prototypow.processed_requests + wysylka.processed_requests
    )

    print("\nWyniki Symulacji:")
    print(
        f"Całkowita liczba zgłoszeń wchodzących do systemu: {len(wszystkie_zgloszenia)}"
    )

    num_green_shipped = len(
        [r for r in wysylka.processed_requests if r.type == "zielony"]
    )
    num_red_shipped = len(
        [r for r in wysylka.processed_requests if r.type == "czerwony"]
    )
    num_blue_shipped = len(
        [r for r in wysylka.processed_requests if r.type == "niebieski"]
    )  # Powinno być zero

    print("\nProdukty wysłane:")
    print(f"  Zielone (standardowe): {num_green_shipped}")
    print(f"  Czerwone (personalizowane): {num_red_shipped}")
    print(
        f"  Niebieskie (prototypy): {num_blue_shipped} (prototypy nie trafiają na wysyłkę)"
    )

    num_blue_prototype = len(
        [r for r in badania_prototypow.processed_requests if r.type == "niebieski"]
    )
    num_green_prototype = len(
        [r for r in badania_prototypow.processed_requests if r.type == "zielony"]
    )
    num_red_prototype = len(
        [r for r in badania_prototypow.processed_requests if r.type == "czerwony"]
    )

    print("\nProdukty, które przeszły przez badania prototypowe:")
    print(f"  Niebieskie (Prototypy): {num_blue_prototype}")
    print(f"  Zielone: {num_green_prototype}")
    print(f"  Czerwone: {num_red_prototype}")

    total_exited = (
        num_green_shipped
        + num_red_shipped
        + num_blue_prototype
        + num_green_prototype
        + num_red_prototype
    )

    print(
        f"\nCałkowita liczba zgłoszeń opuszczających system: {total_exited} (powinno być równe lub mniejsze od liczby zgłoszeń wchodzących do systemu)"
    )

    # Dodatkowe statystyki
    if total_exited > 0:
        avg_time_in_system = total_time_in_system / total_exited
        print(
            f"Średni czas zgłoszenia w systemie: {avg_time_in_system:.2f} jednostek czasu"
        )
    else:
        print("Brak zgłoszeń opuszczających system.")

    # Sprawdzenie, czy jakieś zgłoszenia pozostały w systemie
    remaining_requests = sum(len(stage.queue) for stage in wszystkie_etapy) + sum(
        len(stage.transit_queue) for stage in wszystkie_etapy
    )
    print(
        f"\nLiczba zgłoszeń pozostałych w systemie po zakończeniu symulacji: {remaining_requests}"
    )

    # Wyświetlenie statystyk dla każdego etapu
    print("\nStatystyki etapów:")
    for stage in wszystkie_etapy:
        print(f"Etap: {stage.name}")
        print(f"  Liczba zgłoszeń w kolejce: {len(stage.queue)}")
        print(f"  Liczba zgłoszeń w tranzycie: {len(stage.transit_queue)}")
        print(f"  Przetworzone zgłoszenia: {sum(stage.statistics.values())}")
        print("  Statystyki typów:")
        for type_, count in stage.statistics.items():
            print(f"    {type_.capitalize()}: {count}")
        print(
            f"  Średnia długość kolejki: {sum(stage.queue_lengths)/len(stage.queue_lengths):.2f}"
        )
        print(f"  Maksymalna długość kolejki: {stage.max_queue_length}")
        avg_utilization = (
            sum(stage.utilization) / len(stage.utilization)
            if len(stage.utilization) > 0
            else 0
        )
        print(f"  Średnie wykorzystanie etapu: {avg_utilization:.2f}%")
        print(
            f"  Całkowity czas oczekiwania w kolejce: {stage.total_waiting_time} jednostek czasu"
        )
        print("")

    # Generowanie wykresów
    generate_plots(wszystkie_etapy, current_time, wszystkie_zgloszenia)


def generate_plots(stages: List[Stage], simulation_time: int, requests: List[Request]):
    # Wykres długości kolejek w czasie dla każdego etapu
    plt.figure(figsize=(12, 6))
    for stage in stages[1:]:  # Pomijamy magazyn, bo ma nieskończoną przepustowość
        plt.plot(stage.time, stage.queue_lengths, label=stage.name)
    plt.title("Długości kolejek w czasie")
    plt.xlabel("Czas")
    plt.ylabel("Liczba zgłoszeń w kolejce")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    plt.close()

    # Wykres wykorzystania przepustowości etapów w czasie
    plt.figure(figsize=(12, 6))
    for stage in stages[1:]:  # Pomijamy magazyn
        plt.plot(stage.time, stage.utilization, label=stage.name)
    plt.title("Wykorzystanie etapów w czasie")
    plt.xlabel("Czas")
    plt.ylabel("Wykorzystanie (%)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    plt.close()

    # Histogram czasu spędzonego w systemie
    times_in_system = [r.time_in_system for r in requests if r.time_in_system > 0]
    plt.figure(figsize=(8, 6))
    plt.hist(times_in_system, bins=30, edgecolor="black")
    plt.title("Rozkład czasu spędzonego w systemie")
    plt.xlabel("Jednostki czasu")
    plt.ylabel("Liczba zgłoszeń")
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    plt.close()

    # Liczba przetworzonych zgłoszeń w czasie dla każdego etapu
    plt.figure(figsize=(12, 6))
    for stage in stages[1:]:
        plt.plot(stage.time, stage.processed_per_time, label=stage.name)
    plt.title("Liczba przetworzonych zgłoszeń w czasie")
    plt.xlabel("Czas")
    plt.ylabel("Liczba przetworzonych zgłoszeń")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    plt.close()

    # Wykres liczby przychodzących zgłoszeń w czasie
    arrival_times = [r.arrival_time for r in requests]
    arrivals_per_time = [arrival_times.count(t) for t in range(simulation_time)]
    plt.figure(figsize=(12, 6))
    plt.plot(range(simulation_time), arrivals_per_time, label="Przychodzące zgłoszenia")
    plt.title("Liczba przychodzących zgłoszeń w czasie")
    plt.xlabel("Czas")
    plt.ylabel("Liczba zgłoszeń")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    plt.close()

    # Wykres przepustowości etapów w czasie
    plt.figure(figsize=(12, 6))
    for stage in stages[1:]:
        plt.plot(stage.time, stage.capacity_history, label=stage.name)
    plt.title("Przepustowość etapów w czasie")
    plt.xlabel("Czas")
    plt.ylabel("Przepustowość")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    plt.close()


def main():
    czas_trwania = int(input("Podaj czas trwania symulacji (w jednostkach czasu): "))
    symulacja(czas_trwania)


if __name__ == "__main__":
    main()
