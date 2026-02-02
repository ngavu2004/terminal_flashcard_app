import json
import os
import random
import uuid
from typing import Dict, Any, List, Optional

DATA_FILE = "flashcards.json"


# ----------------------------
# Storage
# ----------------------------
def _default_data() -> Dict[str, Any]:
    return {"collections": {}}


def load_data() -> Dict[str, Any]:
    if not os.path.exists(DATA_FILE):
        return _default_data()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "collections" not in data:
            return _default_data()
        return data
    except (json.JSONDecodeError, OSError):
        return _default_data()


def save_data(data: Dict[str, Any]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ----------------------------
# Helpers (UI)
# ----------------------------
def clear() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def pause(msg: str = "Press Enter to continue...") -> None:
    input(msg)


def prompt_int(prompt: str, lo: int, hi: int) -> int:
    while True:
        s = input(prompt).strip()
        if s.isdigit():
            v = int(s)
            if lo <= v <= hi:
                return v
        print(f"Please enter a number from {lo} to {hi}.")


def prompt_nonempty(prompt: str) -> str:
    while True:
        s = input(prompt).strip()
        if s:
            return s
        print("Input cannot be empty.")


def confirm(prompt: str) -> bool:
    while True:
        s = input(f"{prompt} (y/n): ").strip().lower()
        if s in ("y", "yes"):
            return True
        if s in ("n", "no"):
            return False
        print("Please type y or n.")


def select_from_list(title: str, items: List[str]) -> Optional[str]:
    if not items:
        print("Nothing to select.")
        return None

    print(title)
    for i, name in enumerate(items, start=1):
        print(f"  {i}) {name}")
    print("  0) Cancel")

    choice = prompt_int("Choose: ", 0, len(items))
    if choice == 0:
        return None
    return items[choice - 1]


# ----------------------------
# Domain operations
# ----------------------------
def list_collections(data: Dict[str, Any]) -> List[str]:
    return sorted(data["collections"].keys())


def create_collection(data: Dict[str, Any]) -> None:
    name = prompt_nonempty("New collection name: ")
    if name in data["collections"]:
        print("A collection with that name already exists.")
        return
    data["collections"][name] = {"cards": []}
    save_data(data)
    print(f"Created collection '{name}'.")


def delete_collection(data: Dict[str, Any]) -> None:
    cols = list_collections(data)
    name = select_from_list("Delete which collection?", cols)
    if not name:
        return
    if confirm(f"Delete collection '{name}' and ALL its cards?"):
        del data["collections"][name]
        save_data(data)
        print("Deleted.")


def get_cards(data: Dict[str, Any], col_name: str) -> List[Dict[str, str]]:
    return data["collections"][col_name]["cards"]


def add_card(data: Dict[str, Any], col_name: str) -> None:
    front = prompt_nonempty("Front: ")
    back = prompt_nonempty("Back: ")
    card = {"id": uuid.uuid4().hex[:8], "front": front, "back": back}
    get_cards(data, col_name).append(card)
    save_data(data)
    print(f"Added card {card['id']}.")


def find_card(cards: List[Dict[str, str]], card_id: str) -> Optional[Dict[str, str]]:
    for c in cards:
        if c["id"] == card_id:
            return c
    return None


def list_cards(cards: List[Dict[str, str]]) -> None:
    if not cards:
        print("(No cards yet.)")
        return
    print(f"Cards ({len(cards)}):")
    for c in cards:
        print(f"- {c['id']}: {c['front']}  ->  {c['back']}")


def edit_card(data: Dict[str, Any], col_name: str) -> None:
    cards = get_cards(data, col_name)
    if not cards:
        print("No cards to edit.")
        return

    list_cards(cards)
    card_id = prompt_nonempty("Enter card id to edit: ")
    card = find_card(cards, card_id)
    if not card:
        print("Card id not found.")
        return

    print("Press Enter to keep the current value.")
    new_front = input(f"Front [{card['front']}]: ").rstrip("\n")
    new_back = input(f"Back  [{card['back']}]: ").rstrip("\n")

    if new_front.strip():
        card["front"] = new_front.strip()
    if new_back.strip():
        card["back"] = new_back.strip()

    save_data(data)
    print("Updated.")


def delete_card(data: Dict[str, Any], col_name: str) -> None:
    cards = get_cards(data, col_name)
    if not cards:
        print("No cards to delete.")
        return

    list_cards(cards)
    card_id = prompt_nonempty("Enter card id to delete: ")
    card = find_card(cards, card_id)
    if not card:
        print("Card id not found.")
        return

    if confirm(f"Delete card {card_id}?"):
        cards.remove(card)
        save_data(data)
        print("Deleted.")


def search_cards(cards: List[Dict[str, str]]) -> None:
    if not cards:
        print("No cards to search.")
        return
    q = prompt_nonempty("Search text: ").lower()
    hits = [c for c in cards if q in c["front"].lower() or q in c["back"].lower()]
    if not hits:
        print("No matches.")
        return
    print(f"Matches ({len(hits)}):")
    for c in hits:
        print(f"- {c['id']}: {c['front']}  ->  {c['back']}")


# ----------------------------
# Learn mode
# ----------------------------
def learn_mode(data: Dict[str, Any], col_name: str) -> None:
    cards = list(get_cards(data, col_name))
    if not cards:
        print("No cards to learn yet.")
        return

    print("Learn mode:")
    print("  1) In order")
    print("  2) Random")
    order = prompt_int("Choose: ", 1, 2)
    if order == 2:
        random.shuffle(cards)

    correct = 0
    wrong = 0
    skipped = 0

    for idx, c in enumerate(cards, start=1):
        clear()
        print(f"[{col_name}] Card {idx}/{len(cards)}  (id: {c['id']})")
        print("-" * 40)
        print("FRONT:")
        print(c["front"])
        print("-" * 40)
        input("Press Enter to reveal the back...")

        print("\nBACK:")
        print(c["back"])
        print("-" * 40)

        while True:
            ans = input("Got it? (y/n/skip/q): ").strip().lower()
            if ans in ("y", "yes"):
                correct += 1
                break
            if ans in ("n", "no"):
                wrong += 1
                break
            if ans in ("s", "skip"):
                skipped += 1
                break
            if ans in ("q", "quit"):
                clear()
                print("Session ended early.")
                print(f"Correct: {correct}, Wrong: {wrong}, Skipped: {skipped}")
                return
            print("Please enter y, n, skip, or q.")

    clear()
    print("Done!")
    print(f"Correct: {correct}")
    print(f"Wrong:   {wrong}")
    print(f"Skipped: {skipped}")


# ----------------------------
# Menus
# ----------------------------
def manage_cards_menu(data: Dict[str, Any], col_name: str) -> None:
    while True:
        clear()
        cards = get_cards(data, col_name)
        print(f"Collection: {col_name}  |  Cards: {len(cards)}")
        print("Manage cards")
        print("  1) List cards")
        print("  2) Add card")
        print("  3) Edit card")
        print("  4) Delete card")
        print("  5) Search")
        print("  0) Back")

        choice = prompt_int("Choose: ", 0, 5)
        clear()

        if choice == 0:
            return
        elif choice == 1:
            list_cards(cards)
            pause()
        elif choice == 2:
            add_card(data, col_name)
            pause()
        elif choice == 3:
            edit_card(data, col_name)
            pause()
        elif choice == 4:
            delete_card(data, col_name)
            pause()
        elif choice == 5:
            search_cards(cards)
            pause()


def collection_menu(data: Dict[str, Any], col_name: str) -> None:
    while True:
        clear()
        cards = get_cards(data, col_name)
        print(f"Collection: {col_name}  |  Cards: {len(cards)}")
        print("  1) Learn")
        print("  2) Add card")
        print("  3) Manage cards")
        print("  0) Back")

        choice = prompt_int("Choose: ", 0, 3)
        clear()

        if choice == 0:
            return
        elif choice == 1:
            learn_mode(data, col_name)
            pause()
        elif choice == 2:
            add_card(data, col_name)
            pause()
        elif choice == 3:
            manage_cards_menu(data, col_name)


def open_collection(data: Dict[str, Any]) -> None:
    cols = list_collections(data)
    name = select_from_list("Open which collection?", cols)
    if not name:
        return
    collection_menu(data, name)


def main() -> None:
    data = load_data()

    while True:
        clear()
        cols = list_collections(data)
        print("Terminal Flashcards")
        print("-" * 20)
        print(f"Collections: {len(cols)}")
        print("  1) Create collection")
        print("  2) Open collection")
        print("  3) List collections")
        print("  4) Delete collection")
        print("  0) Exit")

        choice = prompt_int("Choose: ", 0, 4)
        clear()

        if choice == 0:
            print("Bye!")
            return
        elif choice == 1:
            create_collection(data)
            pause()
        elif choice == 2:
            open_collection(data)
        elif choice == 3:
            cols = list_collections(data)
            if not cols:
                print("(No collections yet.)")
            else:
                for c in cols:
                    print(f"- {c} ({len(get_cards(data, c))} cards)")
            pause()
        elif choice == 4:
            delete_collection(data)
            pause()


if __name__ == "__main__":
    main()
