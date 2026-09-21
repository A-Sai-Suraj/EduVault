import json
import streamlit as st
with open("Resources.json","r") as f:
    data=json.load(f)
st.title("# Academic Resource Hub")
year=st.selectbox("Enter year",[1,2])
sem=st.selectbox("Enter Semester",[1,2])
if year==2:
    sem+=2
sem_name=f"semester_{sem}"
sub_name=[]
for sub in data["semesters"][sem_name]["subjects"]:
    sub_name.append(sub["name"])
sub=st.selectbox("Enter Subject",sub_name)
resource=[]
req=data["semesters"][sem_name]["subjects"]
for key in range(len(req)):
    if req[key]["name"]==sub:
        resource=req[key]["resources"]
st.subheader("#RESOURCES")
for i in range(len(resource)):
    st.write(f"{resource[i]['unit']}:\t{resource[i]['url']}\n")

"""sem=input("Enter semester")
sub=input("Enter subject")
req=data["semesters"][sem]["subjects"]
#print(type(req))
resource=[]
for key in range(len(req)):
    if req[key]["name"]==sub:
        resource=req[key]["resources"]
for i in range(len(resource)):
    print(f"{resource[i]['unit']}:\t{resource[i]['url']}\n")"""