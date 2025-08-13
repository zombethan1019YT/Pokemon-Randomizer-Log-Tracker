# Pokémon Randomizer Info Viewer

## Overview

This is a standalone desktop application to view, search, and manage Pokémon data loaded from log files. It supports organizing Pokémon as your team (Player) or as opponents (Enemy), displaying stats, images fetched online, and saving your history.

---

## Features

- Load Pokémon data from `.log` or `.txt` files.
- View detailed stats for your Pokémon or simplified info for enemies.
- Search Pokémon by name.
- Automatically fetch official Pokémon sprites from the internet.
- Save and recall your Player and Enemy Pokémon history.
- Switch between Light, Dark, and Custom color themes.
- Clear Player and Enemy histories separately or both.
- Classify Pokémon when first loaded (Player or Enemy).

---

## How to Use

1. **Open the application**  
   Double-click the executable file to launch the app.

2. **Load a Pokémon log file**  
   Click the **Load Log File** button and select your `.log` or `.txt` file containing Pokémon data.

3. **View Pokémon list**  
   The left list shows your Player Pokémon, Enemy Pokémon, and the full list from the loaded log.

4. **Select a Pokémon**  
   Click a Pokémon name in the list to view its details and image on the right.

5. **Classify Pokémon**  
   When selecting a Pokémon from the log for the first time, a prompt will ask if it’s your Pokémon or an enemy. This classification helps organize your history.

6. **Search Pokémon**  
   Use the search box at the top to type a Pokémon’s name and press Enter or click Search.

7. **Change Theme**  
   Use the dropdown at the top-left to switch between Light Mode, Dark Mode, or create your own Custom Theme.

8. **Clear History**  
   Use the **Clear History** button to erase both Player and Enemy Pokémon records.

---

## Requirements

- No installation needed if you use the provided standalone executable.
- Internet connection required to load Pokémon images.

---

## Troubleshooting

- If images don’t load, check your internet connection.
- Ensure the Pokémon log file follows the correct format with headers like `NUM|NAME|TYPE|HP|ATK|...`.
- If the app crashes or behaves unexpectedly, try restarting it.
- For any issues, please contact the developer.

---

## Developer Notes

This app is built with Python 3 and Tkinter, packaged with PyInstaller for standalone use.
