import os
db_config={
    'user':os.environ.get('db_user'),
    'password':os.environ.get('db_password'),
    'host':os.environ.get('db_host'),
    'database':os.environ.get('database_name')
}
API_TOKEN =os.environ.get('BOT_TOKEN')         
CHANNEL_CID =int(os.environ.get('CHANNEL_CID'))      
admins =eval(os.environ.get('admins')) 
print(f'token: {API_TOKEN}, channel: {CHANNEL_CID}, admins: {admins}') 




