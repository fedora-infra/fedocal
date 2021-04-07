Run following command in the same location where babel.cfg is located 

extract translatable strings from fedocal directory
---------------

pybabel extract -F babel.cfg -k _l -o messages.pot fedocal


Create new language translation, if it does not exist (here adding Finnish as an example)
---------------

pybabel init -i messages.pot -d fedocal/translations -l fi


Update existing translation strings for (any) languages
---------------

pybabel update -i messages.pot -d fedocal/translations

    
Compile existing translations (make the file used by the program itself)
---------------

pybabel compile -d fedocal/translations
