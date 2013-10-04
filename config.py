import os
basedir = os.path.abspath(os.path.dirname(__file__))

# search results
MAX_SEARCH_RESULTS = 50

# pagination
POSTS_PER_PAGE = 3

SQLALCHEMY_DATABASE_URI = 'postgresql://xssvmqvqabqilw:37m-6eL7kd8KjYXRBUNuSnOrTf@ec2-54-247-98-97.eu-west-1.compute.amazonaws.com/blog'
#SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/blog02'
#SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')