from sqlalchemy import Engine
from sqlalchemy.orm import Session

from orm import Config

validating_user = 321297277773938690

active_sessions = {}
failed_login_attempts = {}

path_to_db = 'quotes.db'
session: Session = None
engine: Engine = None
config: Config = None
