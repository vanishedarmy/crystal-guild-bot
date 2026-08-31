# Upgrade Guide — v1.5.0 Trails & Raids

Upgrade from RC1 in place. Back up the live database and preserve `.env`, token storage, hosted secrets, and persistent-disk state. Apply the matching RC1 → v1.5.0 Bot/Web update or replace source with the full production packages. No schema migration or player reset is required. After deployment confirm Bot/Web/frontend runtime `1.5.0-trails-raids`, schema **10**, hosted sync **1**, and Portal protocol **25**.
