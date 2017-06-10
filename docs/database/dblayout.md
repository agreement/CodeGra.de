Het design moet je zien als logica. De primary/foreign keys staan vast maar
metadata informatie (bijv email @ User of description @ File) kunnen naar
gelieve erbij gezet worden. In dit document wordt de opzet van de database in
grote lijnen beschreven, voor meer info kan de file database.svg bekeken worden.

# User table
User kan 1 rol hebben, een foreign key, en meerdere course rollen. Hier kan ook
email, login, etc. geplaatst worden.

# Course table
Standaard informatie van een Course zoals naam/ID. Hier kan ook info in als
locatie, jaargang, etc.

# Assignment table
Iedere course heeft X assignments. In deze table komt de metadata van een
assignment te staan (bijv naam opdracht, beschrijving...).

# Work table
Table van iedere aparte submission van een ingeleverde opdracht van een User.
state veld geeft aan of een TA al is begonnen en/of klaar is (-1,0,1) met
nakijken edit verwijst naar de laatste geplaatse comment van een TA

# File table
Iedere work kan 1 of meer files bevatten. Hier komt de metadata over een file
(bijv extension).

# Comment table
Per file worden de comments bijgehouden van de TA. Hier komt het commentaar en
de bijbehorende regel.

# Permission table
This table contains permissions (such as 'can_edit_grade'), the default value
for a permission and if the permission is a course permission. These are
permissions are linked using two link tables, a roles-permissions table
(linking permissions to the first mentioned (global) roles), and a
course_roles-permissions table linking permissions to course roles.

The global roles are linked to users using a simple foreign key while the course
roles are coupled to users using an extra link table, users-courses, which links
course roles to users. Course roles are linked to courses using a simple foreign
key.

If a user is linked to a permission (for a certain course in the case of course
permissions) the default value of the permission is reversed. So if the
permission `can_edit_email` has the default value of `True` a user can edit its
email iff there is **no** link between the user and this permission. If we have a
permission `can_delete_user` with the default value of `False` a user can delete
a user iff there **is** link between the user and this permission.
