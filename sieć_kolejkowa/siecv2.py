import random
from typing import List, Optional
import matplotlib.pyplot as plt


class Request:
    def __init__(self, id: int, arrival_time: int):
        self.id = id  # Unique identifier
        self.arrival_time = arrival_time
        self.time_in_system = 0
        self.type = self.assign_type()
        self.current_stage = "Magazyn Surowców"
        self.waiting_time = 0  # Total waiting time in queues
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
    def __init__(self, name: str, capacity: int, queue_limit: Optional[int] = None):
        self.name = name  # Stage name
        self.capacity = capacity  # Max number of requests processed per time unit
        self.queue_limit = queue_limit  # Optional queue limit
        self.queue: List[Request] = []  # Queue of requests waiting to be processed
        self.transit_queue: List[Request] = []  # Requests in transit to the next stage
        self.processed_requests: List[
            Request
        ] = []  # Requests that have left the system from this stage
        self.next_stages = []  # List of next stages with conditions
        self.statistics = {
            "zielony": 0,
            "czerwony": 0,
            "niebieski": 0,
        }  # Stats of processed requests by type
        # Lists for data collection for plots and stats
        self.queue_lengths = []
        self.utilization = []
        self.processed_per_time = []
        self.time = []
        self.capacity_history = []
        self.total_waiting_time = 0  # Total waiting time in queue at this stage
        self.max_queue_length = 0  # Maximum queue length at this stage
        self.waiting_times = []  # Waiting times of processed requests at this stage
        self.avg_waiting_times = []  # Average waiting time at each time unit

    def add_next_stage(self, stage, condition):
        self.next_stages.append((stage, condition))

    def receive(self, requests: List[Request]):
        if self.queue_limit is not None:
            available_space = self.queue_limit - len(self.queue)
            if available_space <= 0:
                # Queue is full, reject requests
                return
            else:
                self.queue.extend(requests[:available_space])
        else:
            self.queue.extend(requests)

    def is_empty(self) -> bool:
        return len(self.queue) == 0

    def process(self, current_time: int):
        # Randomize capacity for this time unit
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
        # For 'Magazyn Surowców', capacity is infinite and doesn't change

        # Save capacity history
        self.capacity_history.append(self.capacity)

        # Process requests in order of priority: blue, red, green
        processed_this_unit = []
        waiting_times_this_unit = []
        blues = [r for r in self.queue if r.type == "niebieski"]
        reds = [r for r in self.queue if r.type == "czerwony"]
        greens = [r for r in self.queue if r.type == "zielony"]

        # Total number of processed requests in this time unit
        total_processed = 0

        for requests_of_type in [blues, reds, greens]:
            for request in requests_of_type:
                if total_processed >= self.capacity:
                    break  # Reached max capacity
                self.process_request(request, current_time)
                processed_this_unit.append(request)
                waiting_times_this_unit.append(request.waiting_time)
                total_processed += 1
            if total_processed >= self.capacity:
                break  # Reached max capacity

        # Remove processed requests from queue
        for request in processed_this_unit:
            self.queue.remove(request)

        # Update queue statistics
        self.queue_lengths.append(len(self.queue))
        self.max_queue_length = max(self.max_queue_length, len(self.queue))

        # Update utilization statistics
        utilization_percent = (
            (total_processed / self.capacity) * 100 if self.capacity > 0 else 0
        )
        self.utilization.append(utilization_percent)
        self.processed_per_time.append(total_processed)
        self.time.append(current_time)

        # Update total waiting time
        self.total_waiting_time += sum(r.waiting_time for r in self.queue)

        # Record waiting times
        self.waiting_times.extend(waiting_times_this_unit)

        # Calculate average waiting time for this time unit
        if waiting_times_this_unit:
            avg_waiting_time = sum(waiting_times_this_unit) / len(
                waiting_times_this_unit
            )
        else:
            avg_waiting_time = 0
        self.avg_waiting_times.append(avg_waiting_time)

    def process_request(self, request: Request, current_time: int):
        # Update statistics
        self.statistics[request.type] += 1

        # Set current stage for the request
        request.current_stage = self.name

        # Set request in transit
        request.in_transit = True
        request.next_stage_arrival_time = (
            current_time + 1
        )  # Will arrive after 1 time unit

        # Add request to transit queue
        self.transit_queue.append((request, current_time))

    def update_transit(self, current_time: int):
        # Check if any requests have arrived at the next stage
        arrived_requests = []
        for request, departure_time in self.transit_queue:
            if current_time >= request.next_stage_arrival_time:
                arrived_requests.append(request)

        # Remove requests that have arrived
        self.transit_queue = [
            (r, t) for r, t in self.transit_queue if r not in arrived_requests
        ]

        # Redirect requests to next stages based on conditions
        for request in arrived_requests:
            request.in_transit = False
            for next_stage, condition in self.next_stages:
                if condition(request):
                    next_stage.receive([request])
                    break  # Request goes to only one stage
            else:
                # If no next stage, the request leaves the system
                self.processed_requests.append(request)
                request.time_in_system = current_time - request.arrival_time

    def update_waiting_times(self):
        for request in self.queue:
            request.waiting_time += 1


# Definition of specific stages
class MagazynSurowcow(Stage):
    def __init__(self):
        super().__init__("Magazyn Surowców", capacity=float("inf"))


class LiniaProdukcyjna(Stage):
    def __init__(self):
        super().__init__(
            "Linia Produkcyjna", capacity=0
        )  # Initial value doesn't matter


class Personalizacja(Stage):
    def __init__(self):
        super().__init__("Personalizacja", capacity=0)


class TestyJakosci(Stage):
    def __init__(self):
        super().__init__("Standardowe Testy Jakości", capacity=0)


class BadaniaPrototypow(Stage):
    def __init__(self):
        super().__init__("Badania na Prototypach", capacity=0)


class Wysylka(Stage):
    def __init__(self):
        super().__init__("Wysyłka", capacity=0)


def symulacja(czas_trwania: int):
    # Initialize stages
    magazyn = MagazynSurowcow()
    linia_produkcyjna = LiniaProdukcyjna()
    personalizacja = Personalizacja()
    testy_jakosci = TestyJakosci()
    badania_prototypow = BadaniaPrototypow()
    wysylka = Wysylka()

    # Define flow between stages
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

    # All requests
    wszystkie_zgloszenia = []

    # Main simulation loop
    current_time = 0
    while current_time < czas_trwania:
        # Generate a random number of requests from 20 to 80
        num_new_requests = random.randint(20, 80)
        new_requests = [
            Request(id=len(wszystkie_zgloszenia) + i + 1, arrival_time=current_time)
            for i in range(num_new_requests)
        ]
        wszystkie_zgloszenia.extend(new_requests)

        # Add new requests to the warehouse
        magazyn.receive(new_requests)

        # Process each stage
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

        # Update transits between stages
        for stage in [
            magazyn,
            linia_produkcyjna,
            personalizacja,
            testy_jakosci,
            badania_prototypow,
        ]:
            stage.update_transit(current_time)

        current_time += 1

    # Collecting statistics
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
    total_waiting_times = sum(sum(stage.waiting_times) for stage in wszystkie_etapy)

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
    )  # Should be zero

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

    # Additional statistics
    if total_exited > 0:
        avg_time_in_system = total_time_in_system / total_exited
        avg_waiting_time_overall = total_waiting_times / total_exited
        print(
            f"Średni czas zgłoszenia w systemie: {avg_time_in_system:.2f} jednostek czasu"
        )
        print(
            f"Średni całkowity czas oczekiwania w kolejkach: {avg_waiting_time_overall:.2f} jednostek czasu"
        )
    else:
        print("Brak zgłoszeń opuszczających system.")

    # Check if any requests remain in the system
    remaining_requests = sum(len(stage.queue) for stage in wszystkie_etapy) + sum(
        len(stage.transit_queue) for stage in wszystkie_etapy
    )
    print(
        f"\nLiczba zgłoszeń pozostałych w systemie po zakończeniu symulacji: {remaining_requests}"
    )

    # Display statistics for each stage
    print("\nStatystyki etapów:")
    for stage in wszystkie_etapy:
        print(f"Etap: {stage.name}")
        print(f"  Liczba zgłoszeń w kolejce: {len(stage.queue)}")
        print(f"  Liczba zgłoszeń w tranzycie: {len(stage.transit_queue)}")
        print(f"  Przetworzone zgłoszenia: {sum(stage.statistics.values())}")
        print("  Statystyki typów:")
        for type_, count in stage.statistics.items():
            print(f"    {type_.capitalize()}: {count}")
        avg_queue_length = (
            sum(stage.queue_lengths) / len(stage.queue_lengths)
            if stage.queue_lengths
            else 0
        )
        print(f"  Średnia długość kolejki: {avg_queue_length:.2f}")
        print(f"  Maksymalna długość kolejki: {stage.max_queue_length}")
        avg_utilization = (
            sum(stage.utilization) / len(stage.utilization)
            if len(stage.utilization) > 0
            else 0
        )
        print(f"  Średnie wykorzystanie etapu: {avg_utilization:.2f}%")
        total_waiting_time_stage = sum(stage.waiting_times)
        avg_waiting_time_stage = (
            total_waiting_time_stage / len(stage.waiting_times)
            if stage.waiting_times
            else 0
        )
        print(
            f"  Średni czas oczekiwania w kolejce: {avg_waiting_time_stage:.2f} jednostek czasu"
        )
        print(
            f"  Całkowity czas oczekiwania w kolejce: {total_waiting_time_stage} jednostek czasu"
        )
        print("")

    # Generate plots
    generate_plots(wszystkie_etapy, current_time, wszystkie_zgloszenia)


def generate_plots(stages: List[Stage], simulation_time: int, requests: List[Request]):
    # 1. Queue Length Over Time for each stage
    plt.figure(figsize=(12, 6))
    for stage in stages[1:]:  # Skip 'Magazyn Surowców'
        plt.plot(stage.time, stage.queue_lengths, label=stage.name)
    plt.title("Długości kolejek w czasie")
    plt.xlabel("Czas")
    plt.ylabel("Liczba zgłoszeń w kolejce")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("queue_length_over_time.png")
    plt.close()

    # 2. Distribution of Time Spent in the System
    times_in_system = [r.time_in_system for r in requests if r.time_in_system > 0]
    if times_in_system:
        plt.figure(figsize=(8, 6))
        plt.hist(times_in_system, bins=20, edgecolor="black", label="Czas w systemie")
        avg_time_in_system = sum(times_in_system) / len(times_in_system)
        plt.axvline(
            x=avg_time_in_system,
            color="red",
            linestyle="--",
            label="Średni czas w systemie",
        )
        plt.title("Rozkład czasu spędzonego w systemie przez zgłoszenia")
        plt.xlabel("Czas (jednostki czasu)")
        plt.ylabel("Liczba zgłoszeń")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("time_in_system_distribution.png")
        plt.close()

    # 3. Distribution of Waiting Time in Queues
    all_waiting_times = []
    for stage in stages[1:]:  # Exclude 'Magazyn Surowców'
        all_waiting_times.extend(stage.waiting_times)
    if all_waiting_times:
        plt.figure(figsize=(8, 6))
        plt.hist(
            all_waiting_times,
            bins=20,
            edgecolor="black",
            label="Czas oczekiwania w kolejce",
        )
        avg_waiting_time = sum(all_waiting_times) / len(all_waiting_times)
        plt.axvline(
            x=avg_waiting_time,
            color="red",
            linestyle="--",
            label="Średni czas oczekiwania",
        )
        plt.title("Rozkład czasu oczekiwania w kolejkach")
        plt.xlabel("Czas oczekiwania (jednostki czasu)")
        plt.ylabel("Liczba zgłoszeń")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("waiting_time_distribution.png")
        plt.close()

    # 4. Number of Requests Processed Over Time for each stage
    plt.figure(figsize=(12, 6))
    for stage in stages[1:]:
        plt.plot(stage.time, stage.processed_per_time, label=stage.name)
    plt.title("Liczba przetworzonych zgłoszeń w czasie")
    plt.xlabel("Czas")
    plt.ylabel("Liczba przetworzonych zgłoszeń")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("processed_requests_over_time.png")
    plt.close()

    # 5. Average Waiting Time Over Time for each stage
    plt.figure(figsize=(12, 6))
    for stage in stages[1:]:
        plt.plot(stage.time, stage.avg_waiting_times, label=stage.name)
    plt.title("Średni czas oczekiwania w kolejce w czasie")
    plt.xlabel("Czas")
    plt.ylabel("Średni czas oczekiwania (jednostki czasu)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("average_waiting_time_over_time.png")
    plt.close()

    # 6. Stage Utilization
    stage_names = [stage.name for stage in stages[1:]]
    avg_utilizations = [
        sum(stage.utilization) / len(stage.utilization) if stage.utilization else 0
        for stage in stages[1:]
    ]
    plt.figure(figsize=(10, 6))
    plt.bar(stage_names, avg_utilizations, color="skyblue")
    plt.title("Średnie wykorzystanie etapów")
    plt.xlabel("Etap")
    plt.ylabel("Wykorzystanie (%)")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("stage_utilization.png")
    plt.close()

    # 7. Number of Requests Processed by Each Stage
    total_processed_by_stage = [sum(stage.statistics.values()) for stage in stages[1:]]
    plt.figure(figsize=(10, 6))
    plt.bar(stage_names, total_processed_by_stage, color="green")
    plt.title("Liczba zgłoszeń przetworzonych przez każdy etap")
    plt.xlabel("Etap")
    plt.ylabel("Liczba przetworzonych zgłoszeń")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("requests_processed_by_stage.png")
    plt.close()


def main():
    czas_trwania = int(input("Podaj czas trwania symulacji (w jednostkach czasu): "))
    symulacja(czas_trwania)


if __name__ == "__main__":
    main()
