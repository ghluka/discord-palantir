# 👁️ Discord Palantir

> [!CAUTION]
> This project is for educational and research purposes only.
> Using this software to automate Discord accounts violates Discord’s Terms of Service.
> I am not responsible for any misuse, damages, or account bans resulting from this software.

A Discord osint tool. Dumps all data from a token's guilds to track users in a database.

## 📜 requirements:
- [python](https://python.org) (i ran on v3.13.7)
- [postgresql](https://www.postgresql.org/download/)
- pip install -r requirements.txt

## ⚙️ running:

<details>
<summary>📌 expand to see setup guide (highly recommended)</summary>


- install [postgresql](https://www.postgresql.org/download/)
- go to the directory where you installed postgresql, then navigate to the `/scripts` section, run the `runpsql` script
- it'll open up a login like this:
```
Server [localhost]: localhost
Database [postgres]: postgres
Port [5432]: 5432
Username [postgres]: postgres
Password for user postgres:
```
- just type in all the information you did when installing postgres, you can enter in a specific port 
- then paste or type this into the postgres terminal
```sql
CREATE DATABASE discord_archive;

CREATE USER discord_user WITH PASSWORD 'your_password';
-- set the your_password to something else thats secure

GRANT ALL PRIVILEGES ON DATABASE discord_archive TO discord_user;

\c discord_archive

ALTER SCHEMA public OWNER TO discord_user;
GRANT ALL ON SCHEMA public TO discord_user;

\q
```
- open a terminal again to run psql, instead of going to `/scripts` and running `runpsql`, we're going to `/bin` and running `psql`
- this time we're gonna pass the arguments to psql instead of running the script, so pass these:
```ps
-U discord_user -d discord_archive -f "schema.sql"
```
- replace `schema.sql` with the full path to your `/src/schema.sql` file from this repository
- when you run it, it might ask
```
Password for user discord_user:
```
- just enter the password you came up with when you created discord_user

congrats, you now have an initialized postgre database. now let's finally write the database url, its gonna look like this:
```
postgresql://discord_user:your_password@localhost:5432/discord_archive
```
don't change anything except `your_password@localhost:5432`,
if you set a custom port or ip for your database you'll change `localhost:5432`, otherwise dont.

change `your_password` again to the password you came up with when you created discord_user.

- create in the `/src` directory a file called `.env`
- make this the contents of your `.env`:
```env
DATABASE_URL=""
```
- set the `DATABASE_URL` to your postgresql db url that you just made, it'll look like this:
```env
DATABASE_URL="postgresql://discord_user:your_password@localhost:5432/discord_archive"
```
- optional media cache settings:
```env
MEDIA_CACHE_DIR="media_cache"
MEDIA_CACHE_IMAGE_SIZE="256"
MEDIA_CACHE_WEBP_QUALITY="70"
DISCORD_RETRY_ATTEMPTS="8"
DISCORD_RETRY_BASE_DELAY="2"
DISCORD_RETRY_MAX_DELAY="60"
```
profile pictures and guild icons are cached as small static `.webp` files, even when the original Discord asset is animated.

</details>

---

```sh
cd src # make sure you're in the src directory

# importing a discord account:
py scraper/sync.py --token "" # set to a discord token
py scraper/sync.py --token "" --workers 4 # sync multiple guilds at once

# running the website
py main.py
```

the website includes an api and a browser UI for searching users and guilds.
