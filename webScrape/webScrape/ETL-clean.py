# handle articles data functions
from tools import handle_wordcloud_network_overview, unify_forum_to_db, insert_into_articles, generate_hot_keywords, delete_week_ago_data

# function queue
# 1. webScrape -> get_pttbrain(pages=20), get_storm(), get_businesstoday(pages=5), get_udn(scroll_time=3)
# 2. wordcloud, network, overview -> handle_wordcloud_network_overview()
# 3. unify articles category from different resource -> unify_forum_to_db()
# 4. save the clean articles data into db -> insert_into_articles()
# 5. produce hot keywords from new articles -> generate_hot_keywords()
# 6. delete those not in need data from articles and hotKeywords 7 days ago -> delete_week_ago_data()

# 2. wordcloud, network, overview
handle_wordcloud_network_overview()

# 3. unify articles category from different resource
unify_forum_to_db()

# 4. save the clean articles data into db
insert_into_articles()

# 5. produce hot keywords from new articles
generate_hot_keywords()

# 6. delete 7 days ago related articles records
delete_week_ago_data()
