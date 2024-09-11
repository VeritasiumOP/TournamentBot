from flask import Flask, render_template , request,flash,redirect, session,jsonify
from sqlalchemy import create_engine, MetaData, Table, Column, Integer,String
from sqlalchemy.orm import sessionmaker,declarative_base
import discord
from discord import interactions
from discord.ext import commands
from discord.ui import Button, View, text_input,TextInput,UserSelect
from threading import Thread
import os

TOKEN = os.environ.get('token')






e=create_engine('sqlite:///Sitedata.db')
sess=sessionmaker(bind=e)
ses=sess()
meta=MetaData()
base=declarative_base()



class members(base):
    __tablename__="members"
    DC=Column(String, primary_key=True)
    ID=Column(String)
    RN=Column(String)
    TEAM=Column(Integer)

class teams(base):
     __tablename__="teams"
     DC=Column(String,unique=True) 
     TEAM=Column(Integer,autoincrement=True,primary_key=True)
     TEAMNAME=Column(String)  


base.metadata.create_all(e)



# if not database_exists(engine.url):
#     Base.metadata.create_all(engine)
# else:
#     engine.connect()
# # # 
# ses.add(members(DC="Test1",ID="Test ID",RN="2whr983",TEAM=1))
# ses.add(teams(DC="Test2",TEAM=1))
# ses.commit()



#== === === === === === === == == == === === === === === === === == === == == = = == == == == = == == === == === #


intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


class makeTeamModal(discord.ui.Modal,title='Make a Team!'):
        teamName=(TextInput(label="Team Name:",style=discord.TextStyle.short))
        TeamLeadID=(TextInput(label="Your BGMI ID: ",style=discord.TextStyle.short))
        TeamLeadRN=(TextInput(label="Your College Roll-Number: ",style=discord.TextStyle.short))
        async def on_submit(self, interaction: discord.Interaction):
            DCID=interaction.user.mention
            TeamName=(interaction.data['components'][0]["components"][0]["value"])
            ID=(interaction.data['components'][1]["components"][0]["value"])
            RN=(interaction.data['components'][2]["components"][0]["value"])
            print(DCID,TeamName,ID,RN)
            TeamNumber=((ses.query(teams).order_by(teams.TEAM.desc()).first()).TEAM)+1
            ob=teams(DC=DCID,TEAM=TeamNumber,TEAMNAME=TeamName)
            ob1=members(DC=DCID,RN=RN,TEAM=TeamNumber,ID=ID)
            ses.add(ob)
            ses.add(ob1)
            ses.commit()
            await interaction.response.send_message("Team Created!! Add Memebers now!",ephemeral=True)
        

class addMemberModal(discord.ui.Modal,title='Add a Member!'):
        ID=(TextInput(label="BGMI ID:",style=discord.TextStyle.short))
        RN=(TextInput(label="College RollNumber: ",style=discord.TextStyle.short))

        def __init__(self, DCID):
            self.DCID = DCID
            super().__init__(title='Add a Member!')

        async def on_submit(self, interaction: discord.Interaction):
            ID=(interaction.data['components'][0]["components"][0]["value"])
            RN=(interaction.data['components'][1]["components"][0]["value"])
            teamlead=interaction.user.mention
            DCID=self.DCID
            temnumber=ses.query(teams).filter_by(DC=teamlead).first().TEAM
            ob=members(DC=DCID,RN=RN,TEAM=temnumber,ID=ID)
            ses.add(ob)
            ses.commit()
            view=View()
            addMemberButton=Button(label="Add a Memeber",style=discord.ButtonStyle.green)
            addMemberButton.callback=addMemberButtonClicked
            view.add_item(addMemberButton)
            await interaction.response.send_message("Member Added! Add More?",view=view,ephemeral=True)
        


             

@bot.command(name="teamdetails")
async def homepage(ctx):
    ID=ctx.message.author.mention
    if(ID=="<@576071327983730709>" or ID=="<@928311581337608243>" ):
        data=[]
        TeamsData=ses.query(teams).order_by(teams.TEAM).all()
        lastadded=0
        for i in ses:
            teamNumber=i.TEAM
            membersObjects=ses.query(members).filter_by(TEAM=teamNumber)
            data.append({'teamName':i.TEAMNAME,"members":[]})
    
            for j in membersObjects:
                data[lastadded]['members'].append([j.DC,j.ID,j.RN])

            lastadded+=1
        lastadded=0 

    msg="TEAM DATA REGISTERED SO FAR!! \n ---------------- \n"

    for i in range(len(data)):
        dict=data[i]
        teamname=dict['teamName']
        msg+=f'TEAM: {i+1} \nTEAM NAME: { teamname } \nMembers: '
        for j in dict['members']:
            id=j[0]
            msg+=f" { id } "
        msg+="\n --------------- \n"    

    await ctx.reply(msg)
    print(data)



        



@bot.command(name="start")
async def homepage(ctx):
     
    view=View()
    createButton=Button(label="Create Team",style=discord.ButtonStyle.blurple,row=0)
    addMemberButton=Button(label="Add a Memeber",style=discord.ButtonStyle.green,row=0)
    removeButton=Button(label="Remove a Memeber",style=discord.ButtonStyle.danger,row=1)
    leaveButton=Button(label="Leave Team!",style=discord.ButtonStyle.danger,row=0)
    teamDetailButton=Button(label="Show Team Details",row=1)

    view.add_item(createButton)
    view.add_item(addMemberButton)
    view.add_item(leaveButton)
    view.add_item(removeButton)
    view.add_item(teamDetailButton)
    removeButton.callback=removeButtonClicked
    teamDetailButton.callback=teamDetailButtonClicked
    createButton.callback=createButtonClicked
    addMemberButton.callback=addMemberButtonClicked
    leaveButton.callback=leaveButtonClicked
    
    await ctx.reply("Welcome To BGMI Tournament Registration!" , view=view)




async def removeButtonClicked(interaction: discord.Interaction):
    d1=ses.query(teams).filter_by(DC=interaction.user.mention).all()
    if(len(d1)>0):
        view=View()
        user=UserSelect()
        user.callback=userSelectedForRemovingFunction
        view.add_item(user)
        await interaction.response.send_message("SELECT A TEAM MEMBER FOR REMOVING:",view=view,ephemeral=True)
    else:
        await interaction.response.send_message("You are not a team lead!",ephemeral=True)



async def userSelectedForRemovingFunction(interaction: discord.Interaction):
    userID="<@"+str(interaction.data["values"][0])+">"
    if(interaction.user.mention==userID):
        await interaction.response.send_message("You can not remove yourself like this, click on Leave Team!",ephemeral=True)
    elif(ses.query(members).filter_by(DC=userID).first().TEAM == ses.query(members).filter_by(DC=interaction.user.mention).first().TEAM):
            obj=ses.query(members).filter_by(DC=userID).first()
            ses.delete(obj)
            ses.commit()
            await interaction.response.send_message(f"{userID} Removed from your team!",ephemeral=True)
    else:    
            await interaction.response.send_message(f"{userID} is not in your team",ephemeral=True)

async def teamDetailButtonClicked(interaction: discord.Interaction):
    d1=ses.query(members).filter_by(DC=interaction.user.mention).first()
    d2=ses.query(teams).filter_by(TEAM=d1.TEAM).first()
    d3=ses.query(members).filter_by(TEAM=d1.TEAM).all()
    data=f'''  Your Team Details:
    Team Number :{d2.TEAM}
    Team Name: {d2.TEAMNAME}'''
    for i in range(len(d3)):
        data+= f'''\n Member {i+1} : {d3[i].DC}'''
    await interaction.response.send_message(data,ephemeral=True)



async def leaveButtonClicked(interaction: discord.Interaction):
    view= View()
    b1=Button(label="YES! Leave Team",style=discord.ButtonStyle.danger)
    b1.callback=sureLeaveButtonClicked
    view.add_item(b1)
    view.add_item(Button(label="NO , Dont leave",style=discord.ButtonStyle.green))
    await interaction.response.send_message("ARE YOU SURE?",view=view,ephemeral=True)



async def sureLeaveButtonClicked(interaction: discord.Interaction):
    if(len(ses.query(teams).filter_by(DC=interaction.user.mention).all())==0):
        ses.delete(ses.query(members).filter_by(DC=interaction.user.mention).first())
        ses.commit()
        await interaction.response.send_message("Left Team",ephemeral=True)
    else:
        if(len(ses.query(members).filter_by(TEAM=ses.query(teams).filter_by(DC=interaction.user.mention).first().TEAM).all())==1):
            ses.delete(ses.query(members).filter_by(DC=interaction.user.mention).first())
            ses.delete(ses.query(teams).filter_by(DC=interaction.user.mention).first())        
            ses.commit()
            await interaction.response.send_message("Team Deleted , as you were the only one in the team!",ephemeral=True)
        else:
            await interaction.response.send_message("You are a team lead , you can not leave the team",ephemeral=True)



async def createButtonClicked(interaction: discord.Interaction):
    q=ses.query(members).filter_by(DC =str(interaction.user.mention)).all()
    if (len(q)!=0):     
         await interaction.response.send_message("You Are Already in a team , Contact your TeamLead!",ephemeral=True)
    else:   
        await interaction.response.send_modal(makeTeamModal())
        await interaction.response.send_message("Added!!",ephemeral=True)







async def addMemberButtonClicked(interaction: discord.Interaction):
    q=ses.query(teams).filter_by(DC =str(interaction.user.mention)).all()
    if (len(q)!=0):
        if(len(ses.query(members).filter_by(TEAM=q[0].TEAM).all())>=4):
            await interaction.response.send_message("Your team already has 4 members!",ephemeral=True)
        else:     
            view=View()
            user=UserSelect()
            user.callback=userSelectedFunction
            view.add_item(user)
            await interaction.response.send_message("SELECT A TEAM MEMBER FOR YOUR TEAM:",view=view,ephemeral=True)


    elif(len(ses.query(teams).filter_by(DC =str(interaction.user.mention)).all())!=0):
        await interaction.response.send_message("You are already in a team, Contact TeamLead!",ephemeral=True)
    else:
        await interaction.response.send_message("Make a Team First or ask your TeamLead to add you in the team",ephemeral=True)
        
     


async def userSelectedFunction(interaction: discord.Interaction):
    userID="<@"+str(interaction.data["values"][0])+">"
    q=ses.query(members).filter_by(DC =userID).all()
    
    if (len(q)!=0):     
         await interaction.response.send_message("The Selected Member is already in a team !!",ephemeral=True)
 
    else:   
        q1=ses.query(teams).filter_by(DC =str(interaction.user.mention)).all()
        if(len(ses.query(members).filter_by(TEAM=q1[0].TEAM).all())>=4):
            await interaction.response.send_message("Your team already has 4 members!",ephemeral=True)
        else:     
            await interaction.response.send_modal(addMemberModal(DCID=userID))
    









# async def submitButtonClicked(interaction: discord.Interaction):
#     await interaction.response.send_message("submit!",ephemeral=True)     





# data=[]
# TeamsData=ses.query(teams).order_by(teams.TEAM.desc()).all()
# lastadded=0
# for i in ses:
#     teamNumber=i.TEAM
#     membersObjects=ses.query(members).filter_by(TEAM=teamNumber)
#     data.append({'teamName':i.TEAMNAME,"members":[]})
    
#     for j in membersObjects:
#         data[lastadded]['members'].append([j.DC,j.ID,j.RN])

#     lastadded+=1

# lastadded=0   
        
print()



# =======================================================================#

app = Flask(__name__)




@app.route('/api/member/<DCID>')
def api_member(DCID):
    data={"successfull":False,"teamlead":False}
    print(DCID)
    d1=ses.query(members).filter_by(DC=(str(DCID.strip()))).first()
    d2= ses.query(teams).filter_by(DC=(str(DCID.strip()))).all()
    if(len(d2)>0):
        c1=len(ses.query(members).filter_by(TEAM=ses.query(teams).filter_by(DC=(str(DCID.strip()))).first().TEAM).all())
        print(c1)
        if(c1==1):
            ses.delete(d1)
            ses.delete(d2[0])
            ses.commit()
            data["successfull"]=True
        else:        
            data["teamlead"]=True
    else:
        ses.delete(d1)
        ses.commit()
        data["successfull"]=True
    return jsonify(data)



@app.route('/')
def index():
    data=[]
    TeamsData=ses.query(teams).order_by(teams.TEAM.desc()).all()
    lastadded=0
    for i in ses:
        teamNumber=i.TEAM
        membersObjects=ses.query(members).filter_by(TEAM=teamNumber)
        data.append({'teamName':i.TEAMNAME,"members":[]})
    
        for j in membersObjects:
            data[lastadded]['members'].append([j.DC,j.ID,j.RN])

        lastadded+=1

    lastadded=0 

    print()

    return (render_template("index.html",data=data))


def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# if (__name__=="__main__"):
#     app.run(debug=True)


keep_alive()
bot.run(TOKEN)


