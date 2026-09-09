# Simple Render Setup — Hotfix 5 Gear Favorites Authority Fix

1. Preserve the existing Render persistent disk and secrets.
2. Deploy the matching Bot and Web packages together.
3. Restart the Bot; it will create a verified pre-schema-16 backup and migrate the local DB from schema 15 to 16 automatically.
4. Confirm runtime `1.7.1-resynthesis-a2h5`, schema **16**, hosted sync **1**, and Portal protocol **33**.
5. Confirm PC/mobile Equipment Favorites converge after the Bot processes a Favorite update and normal Portal sync runs.
