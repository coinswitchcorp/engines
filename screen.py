from PIL import ImageGrab

# Capture the entire primary screen
screenshot = ImageGrab.grab()

# Save to disk
screenshot.save("screenshot.png")
