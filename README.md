Record Store
===================
To Run:
createdb record_store
python main_app.py runserver

OR:
http://recordstore-johnvoorhess.herokuapp.com/

----------
Index page is a list page for inventory.
Once signed in, the navigation links change to allow user to visit previously restricted areas.

Users may add records to a wishlist, email the wishlist to themselves, and add records to the database. 

There is currently no distinction made between regular users and administrators, as this was not a requirement. Coming in later versions.

FILE UPLOAD - a sample csv file is included that has been tested and works. Go to /upload to test. 

Screenshots and requirements.txt located in project directory root.

The Record class is modeled after Discogs catalog export tool so that I might do the research and cataloging on Discogs and use their export to populate my own database. Email works corectly on localhost. Still haven't received an email from Heroku. The API is iTunes for artist information. In a later version, I might think about scraping a bio to put on the record_view page.

Please excuse the styles. I am not good at CSS.

Best regards,
John Voorhess