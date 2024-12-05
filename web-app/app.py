import streamlit as st

if "role" not in st.session_state:
    st.session_state.role = None

ROLES = ["Guest", "Admin"]

def login():
    st.header("Log in")
    role = st.selectbox("Choose your role", ROLES)
    if st.button("Log in"):
        st.session_state.role = role
        st.rerun()

def logout():
    st.session_state.role = None
    st.rerun()

role = st.session_state.role
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")
settings = st.Page("pages/settings.py", title="Settings", icon=":material/settings:")
request_1 = st.Page(
    "pages/submit_job.py",
    title="Submit Job",
    icon=":material/handyman:",
    default=(role == "Guest"),
)
request_2 = st.Page(
    "pages/query.py", title="Query", icon=":material/help:"
)
# respond_1 = st.Page(
#     "respond/respond_1.py",
#     title="Respond 1",
#     icon=":material/healing:",
#     default=(role == "Responder"),
# )
# respond_2 = st.Page(
#     "respond/respond_2.py", title="Respond 2", icon=":material/handyman:"
# )
# admin_1 = st.Page(
#     "admin/admin_1.py",
#     title="Admin 1",
#     icon=":material/person_add:",
#     default=(role == "Admin"),
# )
# admin_2 = st.Page("admin/admin_2.py", title="Admin 2", icon=":material/security:")

account_pages = [settings, logout_page]
request_pages = [request_1, request_2]
# respond_pages = [respond_1, respond_2]
# admin_pages = [admin_1, admin_2]

st.title("PPTX Translator")
st.logo("images/logo.png", icon_image="images/icon.png")

page_dict = {}
if st.session_state.role in ["Guest", "Admin"]:
    page_dict["Request"] = request_pages
# if st.session_state.role in ["Responder", "Admin"]:
#     page_dict["Respond"] = respond_pages
# if st.session_state.role == "Admin":
#     page_dict["Admin"] = admin_pages

if len(page_dict) > 0:
    pg = st.navigation(page_dict | {"Account": account_pages} )
else:
    pg = st.navigation([st.Page(login)])

pg.run()