# Тіл білгірлері LIVE — тұрақты база нұсқасы

Бұл нұсқада:
- бөлмелер;
- командалар;
- жауаптар;
- ұпайлар

PostgreSQL базасында сақталады. Render web service қайта іске қосылса да деректер сақталады.

## GitHub
Осы пакеттегі app.py, requirements.txt, render.yaml файлдарын репозиторийге жүктеңіз.

## Render-де база қосу
1. New -> PostgreSQL
2. Name: til-bilgirlery-db
3. База құрылған соң Internal Database URL мәнін көшіріңіз.
4. til-bilgirlery-live -> Environment
5. Environment Variable:
   Key: DATABASE_URL
   Value: Internal Database URL
6. Save Changes
7. Manual Deploy -> Deploy latest commit

ЕСКЕРТУ:
Бұрынғы SQLite-тағы ескі бөлмелер жаңа PostgreSQL базаға автоматты көшпейді.
Бірақ осы нұсқадан кейін жасалған жаңа бөлмелер сақталады.
