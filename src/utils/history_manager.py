from PIL import Image

class HistoryManager:
    def __init__(self):
        self.history = []
        self.history_index = -1

    def save_state(self, image: Image.Image | None):
        """Saves the current state of the image to the history."""
        if image is None:
            return

        # if we are in the middle of history, clear future states
        if self.history_index < len(self.history) - 1:
            self.history = self.history[: self.history_index + 1]

        # add a copy of the current image
        self.history.append(image.copy())
        self.history_index += 1

    def undo(self) -> Image.Image | None:
        """Goes back to the previous state in history."""
        if self.history_index > 0:
            self.history_index -= 1
            return self.history[self.history_index].copy()
        return None

    def redo(self) -> Image.Image | None:
        """Redoes a previously undone action."""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            return self.history[self.history_index].copy()
        return None

    def can_undo(self) -> bool:
        return self.history_index > 0

    def can_redo(self) -> bool:
        return self.history_index < len(self.history) - 1

    def clear(self):
        self.history = []
        self.history_index = -1
