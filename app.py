import streamlit as st
import pandas as pd
import datetime
import os
from typing import Optional

# File paths
LEADS_FILE = "leads.xlsx"
USERS_FILE = "users.xlsx"

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None

# Load and save functions
def load_leads() -> pd.DataFrame:
    if os.path.exists(LEADS_FILE):
        df = pd.read_excel(LEADS_FILE)
        required_cols = ['Status', 'Follow_up_Date', 'Notes', 'Call_Attempts', 
                        'Call_History', 'Assigned_User']
        for col in required_cols:
            if col not in df.columns:
                df[col] = '' if col in ['Notes', 'Call_History', 'Assigned_User'] else \
                         0 if col == 'Call_Attempts' else pd.NaT if col == 'Follow_up_Date' else 'Not Contacted'
        df['Notes'] = df['Notes'].fillna('')
        df['Call_History'] = df['Call_History'].astype(str).fillna('')
        df['Assigned_User'] = df['Assigned_User'].fillna('')
        return df
    return pd.DataFrame(columns=['First Name', 'Last Name', 'Title', 'Email', 'Mobile Phone1',
                                'Mobile Phone2', 'Company Phone', 'Company', 'Company Address',
                                'Status', 'Follow_up_Date', 'Notes', 'Call_Attempts', 
                                'Call_History', 'Assigned_User'])

def load_users() -> pd.DataFrame:
    if os.path.exists(USERS_FILE):
        return pd.read_excel(USERS_FILE)
    return pd.DataFrame(columns=['Username', 'Password', 'Role'])

def save_data(df: pd.DataFrame, filepath: str) -> None:
    df.to_excel(filepath, index=False)

# Authentication
def authenticate(username: str, password: str) -> Optional[str]:
    users_df = load_users()
    user = users_df[(users_df['Username'] == username) & (users_df['Password'] == password)]
    if not user.empty:
        return user.iloc[0]['Role']
    return None

# Main app
def main():
    if not st.session_state.authenticated:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            role = authenticate(username, password)
            if role:
                st.session_state.authenticated = True
                st.session_state.user_role = role
                st.session_state.username = username
                try:
                    st.experimental_rerun()
                except Exception as e:
                    st.error("An error occurred while rerunning the app. Please try again.")
                    st.error(str(e))
            else:
                st.error("Invalid credentials")
        return

    st.title("Lead Management System")
    leads_df = load_leads()
    users_df = load_users()

    # Debug: Check if data is loaded
    if leads_df.empty:
        st.warning("No leads found in leads.xlsx. Please add a lead to get started.")
    if users_df.empty:
        st.error("No users found in users.xlsx. Please ensure the file exists and has users.")

    menu_options = ["Dashboard", "Manage Leads", "Follow-up Schedule"]
    if st.session_state.user_role == "Master":
        menu_options.extend(["User Management", "Performance Reports"])
    choice = st.sidebar.selectbox("Menu", menu_options)

    if choice == "Dashboard":
        st.subheader("Dashboard")
        if st.session_state.user_role == "Master":
            st.dataframe(leads_df)
        else:
            user_leads = leads_df[leads_df['Assigned_User'] == st.session_state.username]
            if user_leads.empty:
                st.info("No leads assigned to you.")
            else:
                st.dataframe(user_leads)

        # Filter options
        status_filter = st.selectbox("Filter by Status", ["All"] + list(leads_df['Status'].unique()))
        if status_filter != "All":
            leads_df = leads_df[leads_df['Status'] == status_filter]
        
        start_date = st.date_input("Start Date", value=datetime.date.today())
        end_date = st.date_input("End Date", value=datetime.date.today() + datetime.timedelta(days=7))
        leads_df['Follow_up_Date'] = pd.to_datetime(leads_df['Follow_up_Date']).dt.date
        leads_df = leads_df[(leads_df['Follow_up_Date'] >= start_date) & (leads_df['Follow_up_Date'] <= end_date)]

        st.dataframe(leads_df)

    elif choice == "Manage Leads":
        st.subheader("Manage Leads")

        # Tabs for managing leads
        tab1, tab2 = st.tabs(["Add/Edit Lead", "Bulk Assign Leads"])

        with tab1:
            # Check if there are leads to manage
            if leads_df.empty:
                st.info("No leads available. Add a new lead to get started.")
            else:
                lead_names = [f"{row['First Name']} {row['Last Name']}" for _, row in leads_df.iterrows()]
                lead_names.append("New Lead")
                selected_lead = st.selectbox("Select Lead", lead_names)

                if selected_lead == "New Lead":
                    # Normal users cannot add new leads
                    if st.session_state.user_role != "Master":
                        st.error("Only Master users can add new leads.")
                    else:
                        with st.form("new_lead_form"):
                            st.write("Add New Lead")
                            col1, col2 = st.columns(2)
                            with col1:
                                first_name = st.text_input("First Name")
                                last_name = st.text_input("Last Name")
                                title = st.text_input("Title")
                                email = st.text_input("Email")
                            with col2:
                                mobile1 = st.text_input("Mobile Phone 1")
                                mobile2 = st.text_input("Mobile Phone 2")
                                company_phone = st.text_input("Company Phone")
                                company = st.text_input("Company")
                            company_address = st.text_area("Company Address")
                            
                            status = st.selectbox("Status", ["Not Contacted", "Contacted", "Interested", 
                                                           "Not Interested", "Follow Up Needed"])
                            follow_up_date = st.date_input("Follow-up Date", min_value=datetime.date.today())
                            notes = st.text_area("Notes")
                            
                            # Lead assignment
                            if st.session_state.user_role == "Master":
                                if users_df.empty:
                                    st.error("No users available to assign leads. Please add users first.")
                                    assigned_user = ""
                                else:
                                    assigned_user = st.selectbox("Assign to User", users_df['Username'].tolist())
                            else:
                                assigned_user = st.session_state.username

                            if st.form_submit_button("Add Lead"):
                                if not first_name or not last_name:
                                    st.error("First Name and Last Name are required!")
                                else:
                                    new_lead = pd.DataFrame({
                                        'First Name': [first_name], 'Last Name': [last_name], 'Title': [title],
                                        'Email': [email], 'Mobile Phone1': [mobile1], 'Mobile Phone2': [mobile2],
                                        'Company Phone': [company_phone], 'Company': [company],
                                        'Company Address': [company_address], 'Status': [status],
                                        'Follow_up_Date': [follow_up_date], 'Notes': [notes],
                                        'Call_Attempts': [0], 'Call_History': [''], 'Assigned_User': [assigned_user]
                                    })
                                    save_data(pd.concat([leads_df, new_lead], ignore_index=True), LEADS_FILE)
                                    st.success("Lead added successfully!")
                                    st.experimental_rerun()

                else:
                    lead_index = lead_names.index(selected_lead)
                    current_data = leads_df.iloc[lead_index]
                    
                    # Check if the user has permission to edit this lead
                    if st.session_state.user_role != "Master" and current_data['Assigned_User'] != st.session_state.username:
                        st.error("You can only edit your assigned leads.")
                        return

                    with st.form("update_lead_form"):
                        st.write(f"Updating: {selected_lead}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.session_state.user_role == "Master":
                                first_name = st.text_input("First Name", value=current_data['First Name'])
                                last_name = st.text_input("Last Name", value=current_data['Last Name'])
                                title = st.text_input("Title", value=current_data['Title'])
                                email = st.text_input("Email", value=current_data['Email'])
                            else:
                                st.write(f"**First Name:** {current_data['First Name']}")
                                st.write(f"**Last Name:** {current_data['Last Name']}")
                                st.write(f"**Title:** {current_data['Title']}")
                                st.write(f"**Email:** {current_data['Email']}")
                        with col2:
                            if st.session_state.user_role == "Master":
                                mobile1 = st.text_input("Mobile Phone 1", value=current_data['Mobile Phone1'])
                                mobile2 = st.text_input("Mobile Phone 2", value=current_data['Mobile Phone2'])
                                company_phone = st.text_input("Company Phone", value=current_data['Company Phone'])
                                company = st.text_input("Company", value=current_data['Company'])
                            else:
                                st.write(f"**Mobile Phone 1:** {current_data['Mobile Phone1']}")
                                st.write(f"**Mobile Phone 2:** {current_data['Mobile Phone2']}")
                                st.write(f"**Company Phone:** {current_data['Company Phone']}")
                                st.write(f"**Company:** {current_data['Company']}")
                        
                        if st.session_state.user_role == "Master":
                            company_address = st.text_area("Company Address", value=current_data['Company Address'])
                        else:
                            st.write(f"**Company Address:** {current_data['Company Address']}")

                        # Fields editable by both Master and Normal users
                        status = st.selectbox("Status", ["Not Contacted", "Contacted", "Interested", 
                                                        "Not Interested", "Follow Up Needed"],
                                             index=["Not Contacted", "Contacted", "Interested", 
                                                    "Not Interested", "Follow Up Needed"].index(current_data['Status']))
                        follow_up_date = st.date_input("Follow-up Date", 
                                                       value=pd.to_datetime(current_data['Follow_up_Date']).date() if pd.notna(current_data['Follow_up_Date']) else datetime.date.today())
                        notes = st.text_area("Notes", value=current_data['Notes'])
                        made_call = st.checkbox("Log call attempt")
                        
                        # Lead assignment (only for Master users)
                        if st.session_state.user_role == "Master":
                            if users_df.empty:
                                st.error("No users available to assign leads. Please add users first.")
                                assigned_user = current_data['Assigned_User']
                            else:
                                assigned_user = st.selectbox("Assign to User", users_df['Username'].tolist(),
                                                             index=users_df['Username'].tolist().index(current_data['Assigned_User']) if current_data['Assigned_User'] in users_df['Username'].tolist() else 0)
                        else:
                            assigned_user = st.session_state.username
                            st.write(f"**Assigned User:** {current_data['Assigned_User']}")

                        if st.form_submit_button("Update Lead"):
                            # For Master users, update all fields
                            if st.session_state.user_role == "Master":
                                if not first_name or not last_name:
                                    st.error("First Name and Last Name are required!")
                                    return
                                leads_df.at[lead_index, 'First Name'] = first_name
                                leads_df.at[lead_index, 'Last Name'] = last_name
                                leads_df.at[lead_index, 'Title'] = title
                                leads_df.at[lead_index, 'Email'] = email
                                leads_df.at[lead_index, 'Mobile Phone1'] = mobile1
                                leads_df.at[lead_index, 'Mobile Phone2'] = mobile2
                                leads_df.at[lead_index, 'Company Phone'] = company_phone
                                leads_df.at[lead_index, 'Company'] = company
                                leads_df.at[lead_index, 'Company Address'] = company_address
                            
                            # Update fields editable by both Master and Normal users
                            if made_call:
                                leads_df.at[lead_index, 'Call_Attempts'] = current_data['Call_Attempts'] + 1
                                call_entry = f"{datetime.datetime.now()}: Status: {status}, Notes: {notes}\n"
                                leads_df.at[lead_index, 'Call_History'] = str(current_data['Call_History']) + call_entry
                            leads_df.at[lead_index, 'Status'] = status
                            leads_df.at[lead_index, 'Follow_up_Date'] = follow_up_date
                            leads_df.at[lead_index, 'Notes'] = notes
                            leads_df.at[lead_index, 'Assigned_User'] = assigned_user
                            save_data(leads_df, LEADS_FILE)
                            st.success("Lead updated successfully!")
                            st.experimental_rerun()

        with tab2:
            st.subheader("Bulk Assign Leads")
            if st.session_state.user_role != "Master":
                st.error("Only Master users can bulk assign leads.")
            else:
                if leads_df.empty:
                    st.info("No leads available to assign.")
                elif users_df.empty:
                    st.error("No users available to assign leads. Please add users first.")
                else:
                    st.write("Select leads to assign:")
                    selected_leads = []
                    for i, row in leads_df.iterrows():
                        lead_name = f"{row['First Name']} {row['Last Name']}"
                        if st.checkbox(f"{lead_name} (Current: {row['Assigned_User'] or 'Unassigned'})", key=f"bulk_{i}"):
                            selected_leads.append(i)

                    if not selected_leads:
                        st.info("Please select at least one lead to assign.")
                    else:
                        with st.form("bulk_assign_form"):
                            assign_to_user = st.selectbox("Assign selected leads to:", users_df['Username'].tolist())
                            if st.form_submit_button("Assign Leads"):
                                for lead_index in selected_leads:
                                    leads_df.at[lead_index, 'Assigned_User'] = assign_to_user
                                save_data(leads_df, LEADS_FILE)
                                st.success(f"Assigned {len(selected_leads)} leads to {assign_to_user}!")
                                st.experimental_rerun()

    elif choice == "Follow-up Schedule":
        st.subheader("Follow-up Schedule")
        
        # Date range selection for follow-ups
        start_date = st.date_input("Start Date", value=datetime.date.today())
        end_date = st.date_input("End Date", value=datetime.date.today() + datetime.timedelta(days=7))
        
        # Show leads needing follow-up within date range
        leads_df['Follow_up_Date'] = pd.to_datetime(leads_df['Follow_up_Date']).dt.date
        upcoming_follow_ups = leads_df[leads_df['Follow_up_Date'].notna() & 
                                      (leads_df['Follow_up_Date'] >= start_date) & 
                                      (leads_df['Follow_up_Date'] <= end_date)]
        
        if not upcoming_follow_ups.empty:
            upcoming_follow_ups = upcoming_follow_ups.sort_values('Follow_up_Date')
            st.dataframe(upcoming_follow_ups)
        else:
            st.write("No follow-ups scheduled in this date range.")
            
    elif choice == "User Management" and st.session_state.user_role == "Master":
        st.subheader("User Management")
        
        with st.form("user_form"):
            st.write("Add New User")
            new_username = st.text_input("New Username")
            new_password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["Master", "Normal"])
            if st.form_submit_button("Add User"):
                if new_username in users_df['Username'].values:
                    st.error("Username already exists!")
                elif not new_username or not new_password:
                    st.error("Username and password cannot be empty!")
                else:
                    new_user = pd.DataFrame({'Username': [new_username], 
                                           'Password': [new_password], 
                                           'Role': [role]})
                    save_data(pd.concat([users_df, new_user], ignore_index=True), USERS_FILE)
                    st.success(f"User {new_username} added successfully!")
                    st.experimental_rerun()

        st.write("Current Users:")
        if not users_df.empty:
            for i, row in users_df.iterrows():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                col1.write(row['Username'])
                col2.write(row['Role'])
                col3.write("****")
                if row['Username'] != st.session_state.username:
                    if col4.button("Delete", key=f"del_{i}"):
                        leads_df.loc[leads_df['Assigned_User'] == row['Username'], 'Assigned_User'] = ''
                        save_data(leads_df, LEADS_FILE)
                        users_df = users_df[users_df['Username'] != row['Username']]
                        save_data(users_df, USERS_FILE)
                        st.success(f"User {row['Username']} deleted!")
                        st.experimental_rerun()
        else:
            st.write("No users found.")

    elif choice == "Performance Reports" and st.session_state.user_role == "Master":
        st.subheader("Performance Reports")
        if leads_df.empty:
            st.info("No leads available to generate reports.")
        else:
            user_performance = leads_df.groupby('Assigned_User').agg({
                'Call_Attempts': 'sum',
                'Status': lambda x: pd.Series(x).value_counts().to_dict()
            }).reset_index()
            st.dataframe(user_performance)

if __name__ == "__main__":
    if not os.path.exists(LEADS_FILE):
        initial_leads = pd.DataFrame([
            ['Miriam', 'Maslin', 'Founder', 'miriam@revoltmodels.com', '+44 73 4155 4443', '', '', 'Revolt Model Agency', 'United Kingdom', 'Not Contacted', pd.NaT, '', 0, '', '']
        ], columns=['First Name', 'Last Name', 'Title', 'Email', 'Mobile Phone1',
                   'Mobile Phone2', 'Company Phone', 'Company', 'Company Address',
                   'Status', 'Follow_up_Date', 'Notes', 'Call_Attempts', 
                   'Call_History', 'Assigned_User'])
        save_data(initial_leads, LEADS_FILE)

    if not os.path.exists(USERS_FILE):
        initial_users = pd.DataFrame([
            {'Username': 'admin', 'Password': 'admin123', 'Role': 'Master'},
            {'Username': 'john', 'Password': 'pass123', 'Role': 'Normal'}
        ])
        save_data(initial_users, USERS_FILE)

    main()
