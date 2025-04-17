import streamlit as st
import supabase, requests, random, datetime, hashlib, logging
from supabase_helper import SupabaseStorage
import streamlit.components.v1 as components
from dateutil import parser

# Google Analytics Code
ga_code = """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-K73LNWTHQB"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-K73LNWTHQB');
</script>
"""

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def get_user_ip():
    try:
        ip = requests.get("https://api.ipify.org").text
        return ip
    except:
        return "Unknown"
    

def generate_md5_hash(input_string):
    # Encode the input string to bytes
    encoded = input_string.encode()
    
    # Create the MD5 hash object
    md5_hash = hashlib.md5(encoded)
    
    # Return the raw (hexadecimal) digest
    return md5_hash.hexdigest()

def login():
    st.title("🔐 Admin Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    password_hash = generate_md5_hash(password)
    login_button = st.button("Login")

    if login_button:
        user_ip = get_user_ip()
        data = storage.get_username_password_data(username, password_hash, "users") 
        if data:
            st.session_state.logged_in = True
            st.session_state.username = data['username']
            st.session_state.role = data['role']
            st.success(f"✅ Successfully, Logged in as {st.session_state.username}!")
            logging.critical(f"✅ Admin login successful: {username} | IP: {user_ip}")
        else:
            st.error("❌ Invalid credentials")
            logging.warning(f"❌ Failed login attempt for user: {username} | IP: {user_ip}")


# Main
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


def home():
    st.subheader("Welcome to our Community! 🎓")
    # st.image("./welcome.gif", width=400)
    st.markdown(
    """
    <div style="text-align: center;">
        <img src="https://media1.tenor.com/m/Ifusx2INg3wAAAAd/i-would-like-to-extend-a-heartfelt-welcome-to-you-all-squid-game.gif" alt="Study Vibes" width="400"/>
    </div>
    """,
    unsafe_allow_html=True
)
    st.markdown("### Khoon + paseena + mehnat = mess (so be clean guys✌)")
    st.markdown("""
<div style="padding-top:2rem">
<p>Hey there, welcome to the community — made for the students, by the students of <strong>SIET</strong>. This isn’t just another boring college portal. Here, we’re trying to dodge the chaos of the system and actually help each other out (because let’s be real, we’re all in the same boat 🚤).
Whether it’s sharing notes, dropping assignment solutions, catching up on announcements, or just vibing over shared struggles 
— this space is all about connection, support, and making college life a little less stressful. So jump in, share the knowledge, 
and let’s work together. 🤝📚✨</p></div>""", unsafe_allow_html=True)
    
    markdown = """
### 🚀 Features You'll Love

Here's are some features that you might find useful:

---

#### 📂 Assignment Solutions  
No more last-minute scrambling — access, upload, and share solutions for all your subjects in one place. Help out a friend or find what you need fast.

---

#### 📝 Class Notes Archive  
Missed a lecture? Don’t stress. Browse or contribute class notes, organized by subject names. Studying just got smarter.

---

#### 📢 Announcements Hub  
Stay in the loop without digging through 15 group chats. Get real-time updates from student reps, faculty, or clubs — all in one clean feed.

---

> We're building this for us, together — so keep sharing feedback and ideas to make it even better! 🙌  
> **In case of any bugs/suggestions please navigate to the :blue[Rate Us] section! ✨** 
---

> _Built by students, for students._  
> Let's make learning easier, together! 💡


"""
    st.markdown(markdown)


def assignments():
    st.subheader("📌 Solved Assignments")
    year_ops = {
            "1st Year": 1,
            "2nd Year": 2,
            "3rd Year": 3,
            "4th Year": 4
            
        }
    
    # Search bar
    search_query = st.text_input("🔍 Search Assignments", "")
    assignments = storage.get_data("assignments")

    if assignments:
        if search_query:
            filtered_assignments = [assignment for assignment in assignments if search_query.strip().lower() in (assignment['subject'].lower() or assignment['title'].lower())]
        else:
            filtered_assignments = assignments
        
        for assignment in reversed(filtered_assignments):
            with st.expander(assignment["title"]):
                st.write(f"**Subject:** {assignment['subject']}")
                st.write(f"**Year:** {assignment['year']}")

                formatted_time = format_timestamp(assignment['created_at'])
                st.write(f"Upload Date: {formatted_time}")

                if assignment["pdf_file"]:
                    res = requests.get(assignment['pdf_file'])
                    if res.status_code == 200:
                        pdf_data = res.content
                        st.download_button(
                            label="📄 Download PDF",
                            data=pdf_data,
                            file_name=f"{assignment['subject']}_assignment.pdf",
                            mime="application/pdf",
                            key=f"download-button-{assignment['subject']}-{assignment['id']}"
                        )
                    else:
                        st.error("Failed to retrieve PDF!")

                # Delete button
                if (st.session_state.logged_in ==True) and (st.session_state.role == "admin"):
                    delete_button = st.button(f"🚮 Delete Assignment", key=f"delete-button-{assignment['id']}")
                    if delete_button:
                        if storage.delete_record(table_name="assignments", column="id", value=assignment["id"]):
                            st.success("Assignment deleted successfully!", icon="🎉")
                        else:
                            st.error("Failed to delete assignment!", icon="❌")

    st.markdown("---")

    st.subheader("📃 Upload Assignment Solutions")
    with st.form("add_assignment"):
        year = st.selectbox("Select Year", list(year_ops.keys()))
        title = st.text_input("Assignment Title")
        subject = st.text_input("Subject")
        
        pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
        submit = st.form_submit_button("Upload Assignment")

        if submit and title and year:
            if subject:
                if pdf_file:
                    file_name = storage.upload_file(pdf_file.read(), pdf_file.name, 'assignments')
                    url = storage.get_file_url(file_name, "assignments")

                    assignment_data = {
                        "year": year_ops[year],
                        "title": title,
                        "subject": subject,
                        "pdf_file": url,
                        "file_name": file_name
                    }

                    res = storage.insert_data(assignment_data, "assignments")
                    if res:
                        st.success('Assignment uploaded successfully!', icon='🎉')
                    else:
                        st.error("❌ Error uploading Assignment!")
                else:
                    st.error(":warning: Please upload a PDF file!")
            else:
                st.error(":warning: Please enter subject name!")

def notes():
    st.subheader("📒 Subject Notes")

    year_ops = {
            "1st Year": 1,
            "2nd Year": 2,
            "3rd Year": 3,
            "4th Year": 4
            
        }
    
    # Search bar
    search_query = st.text_input("🔍 Search Notes", "")
    notes = storage.get_data("notes")

    if notes:
        if search_query.strip():
            filtered_notes = [each for each in notes if search_query.strip().lower() in each['subject_name'].lower()]
   
        else:
            filtered_notes = notes

        for each in reversed(filtered_notes):
            with st.expander(f"**Subject:** {each['subject_name']}"):
                remarks = str(each['remarks']).splitlines()
                st.write("**Remarks:**")
                for line in remarks:
                    st.write(f"- {line}")

                st.write(f"**Year:** {each['year']}")

                if each["pdf_file"]:
                    res = requests.get(each['pdf_file'])
                    if res.status_code == 200:
                        pdf_data = res.content
                        st.download_button(
                            label="📄 Download PDF",
                            data=pdf_data,
                            file_name=f"{each['subject_name']}_notes.pdf",
                            mime="application/pdf",
                            key=f"download-button-{each['subject_name']}-{each['id']}"
                        )
                    else:
                        st.error("Failed to retrieve PDF!")

                # Delete button
                if (st.session_state.logged_in ==True) and (st.session_state.role == "admin"):
                    delete_button = st.button(f"🚮 Delete Notes", key=f"delete-button-{each['id']}")
                    if delete_button:
                        data = storage.delete_record(table_name="notes", column="id", value=each["id"])
                        if data:
                            st.success("Notes deleted successfully!", icon="🎉")
                        else:
                            st.error("Failed to delete notes!", icon="❌")
    
    st.markdown("---")

    st.subheader("🗂️ Upload Notes")
    
    year = st.selectbox("Select Year", list(year_ops.keys()))
    subject = st.text_input("Enter Subject Name")
    note_text = st.text_area("Remarks/Suggestions (Optional)", placeholder="Type your remarks here... Press Enter for a new line.")
    pdf_note = st.file_uploader("Upload PDF Note", type=["pdf"])
    save_note = st.button("Upload Notes")

    if save_note and subject and year:
        if pdf_note:
            # Upload the PDF note to Supabase
            pdf_data = pdf_note.read()
            pdf_name = pdf_note.name
            file_name = storage.upload_file(pdf_data, pdf_name, 'notes')
            url = storage.get_file_url(file_name, 'notes')

            notes_data = {
                "year": year_ops[year],
                "subject_name": subject,
                "remarks": note_text,
                "pdf_file": url,
                "file_name": file_name
            }

            res = storage.insert_data(notes_data, "notes")
            if res:
                st.success('Notes uploaded successfully!', icon='🎉')
            else:
                st.error("❌ Error uploading Notes.")
        else:
            st.error(":warning: Please upload a PDF file!")

def announcements():
    st.subheader("📬 College Announcements")

    # View announcements
    supabase_data = storage.get_data("announcements")
    if supabase_data:
        for idx, a in enumerate(reversed(supabase_data)):
            st.info(f"📢 **{a['title']}**")
            st.caption(a["desc"])

            # Delete button
            if (st.session_state.logged_in ==True) and (st.session_state.role == "admin"):
                delete_button = st.button(f"🚮 Delete Announcement", key=f"delete-button-{a['id']}")
                if delete_button:
                    if storage.delete_record(table_name="announcements", column="id", value=a["id"]):
                        st.success("Announcement deleted successfully!", icon="🎉")
                    else:
                        st.error("Failed to delete announcement!", icon="❌")
            
    else:
        st.error("No announcements found")

    st.markdown("---")

    
    with st.expander("📮 Post New Announcement"):
        new_announcement_title = st.text_input("Announcement Title")
        new_announcement = st.text_area("Announcement")
        post = st.button("Post Announcement")

        if post:
            if new_announcement_title:
                supabase_data = storage.insert_data({
                    "title": new_announcement_title,
                    "desc": new_announcement
                }, "announcements")
                if supabase_data:
                    st.balloons()
                    st.toast('New announcement posted!', icon='🎉')
                else:
                    st.error("❌ Error posting announcement.")
            else:
                st.error(":warning: Please fill in the title at least!")


def sess_pyqs():
    st.subheader("📘 Sessional PYQs")
   
    year_ops = {
            "1st Year": 1,
            "2nd Year": 2,
            "3rd Year": 3,
            "4th Year": 4
            
        }
    
    sess_ops = ["Sessional 1", "Sessional 2", "Sessional 3"]

    # Search bar
    search_query = st.text_input("🔍 Search PYQs", "")
    pyqs = storage.get_data("sessional_pyqs")

    if search_query:
        filtered_pyqs = [pyq for pyq in pyqs if search_query.strip().lower() in pyq['subject'].lower()]
    else:
        filtered_pyqs = pyqs


    for each in reversed(filtered_pyqs):
            with st.expander(f"**Subject:** {each['subject']}"):
                remarks = str(each['desc']).splitlines()
                st.write("**Remarks:**")
                for line in remarks:
                    st.write(f"- {line}")

                st.write(f"**Year:** {each['year']}")
                st.write(f"**Sessional:** {each['sess_no']}")
                

                formatted_time = format_timestamp(each['created_at'])
                st.write(f"Upload Date: {formatted_time}")

                if each["pdf_file"]:
                    res = requests.get(each['pdf_file'])
                    if res.status_code == 200:
                        pdf_data = res.content
                        st.download_button(
                            label="📄 Download PDF",
                            data=pdf_data,
                            file_name=f"{each['subject']}_pyq.pdf",
                            mime="application/pdf",
                            key=f"download-button-{each['subject']}-{each['id']}"
                        )
                    else:
                        st.error("Failed to retrieve PDF!")

                # Delete button
                if (st.session_state.logged_in ==True) and (st.session_state.role == "admin"):
                    delete_button = st.button(f"🚮 Delete PYQ", key=f"delete-button-{each['id']}")
                    if delete_button:
                        if storage.delete_record(table_name="sessional_pyqs", column="id", value=each["id"]):
                            st.success("PYQ deleted successfully!", icon="🎉")
                        else:
                            st.error("Failed to delete pyq!", icon="❌")
                    
    st.markdown("---")

    st.subheader("🗂️ Upload PYQs")
    
    
    year = st.selectbox("Select Year", list(year_ops.keys()))
    sess_no = st.selectbox("Select Sessional", sess_ops)
    subject = st.text_input("Enter Subject Name")
    note_text = st.text_area("Remarks/Suggestions (Optional)", placeholder="Type your remarks here... Press Enter for a new line.")
    pdf_pyq = st.file_uploader("Upload PDF", type=["pdf"])
    save_pdf = st.button("Upload PYQ")

    if subject and save_pdf and year:
        if pdf_pyq:
            # Upload the PDF to Supabase
            pdf_data = pdf_pyq.read()
            pdf_name = pdf_pyq.name
            file_name = storage.upload_file(pdf_data, pdf_name, 'sessional_pyqs')
            url = storage.get_file_url(file_name, 'sessional_pyqs')

            pyq_data = {
                "year": year_ops[year],
                "sess_no": sess_no,
                "subject": subject,
                "desc": note_text,
                "pdf_file": url,
                "file_name": file_name
            }

            res = storage.insert_data(pyq_data, "sessional_pyqs")
            if res:
                st.toast('PYQ uploaded successfully!', icon='🎉')
            else:
                st.error("❌ Error uploading PYQ.")
        else:
            st.error(":warning: Please upload a PDF file!")


def feedback_form():
    prof_data = storage.get_data("professors")
    professors = {prof['id']: prof for prof in prof_data}
   
    profs = [x['name'] for x in list(professors.values())]


    st.subheader("Your Feedback Matters...")
    st.info("👋 Hey, we need some of your details for security reasons but don't worry none of your details will be shared with anyone (until you follow the rules mentioned below)")
    st.markdown("""> :blue[Please read the rules before submitting a review:]  
> 1. **No :red[inappropriate language] will be entertained towards any faculty**!  
> 2. **The remarks/feedback must contain :green[valid points] otherwise just leave it blank**""")
    # Step 1: Select Professor
    selected_professor = st.selectbox("Select Professor", profs)

    # Step 2: Rating Section
    rating = st.slider("Rate the professor (1-5)", 1, 5)

    # Step 3: Feedback Section
    title = st.text_area("Title")
    feedback = st.text_area("Leave your feedback (optional)")
    
    std_id = st.text_input("College Student ID (will not be shared)")


    if st.button("Submit Feeback") and title and selected_professor:
        # Insert the feedback into the Supabase table
        if std_id:
            prof_id = 0
            for key,val in professors.items():
                if val['name'] == selected_professor:
                    prof_id = key
        
            supabase_data = storage.insert_data({
                "prof_name": prof_id,
                "title": title,
                "desc": feedback,
                "rating": rating,
                "std_id": std_id
            }, "professor_reviews")

            if supabase_data:
                st.balloons()
                st.success('Feedback submitted! Thanks for your input.', icon='🎉')
            else:
                st.error("❌ Failed to submit feedback")
        else:
            st.info("Please enter your student ID. Don't worry it will remain confidential..🤗", icon="ℹ️")


    st.markdown("---")

    st.subheader('📜 The Ultimate "Feedback Form"')
   
 

    check_prof = st.selectbox("Select Professor", profs, key="check_prof")
    
    # average_rating = "⭐ 4.7 / 5.0"

    image_url = "https://t3.ftcdn.net/jpg/03/53/11/00/360_F_353110097_nbpmfn9iHlxef4EDIhXB1tdTD0lcWhG9.jpg"

    if check_prof:
        # HTML block with flex layout
        average_rating = 0
        average_rating = sum([x['rating'] for x in storage.get_data("professor_reviews") if professors.get(x['prof_name'])['name'] == check_prof])/5.0
        average_rating = f"⭐ {average_rating} / 5.0"
        prof_image = ""
        
        for key,value in professors.items():
            if value['name'] == check_prof:
                prof_image = value['image_url']

        reviews = [x for x in storage.get_data("professor_reviews") if professors.get(x['prof_name'])['name'] == check_prof]

        st.markdown(
            f"""
            <div style="
                border: 1px solid #ccc; 
                border-radius: 10px; 
                padding: 15px; 
                background-color: black; 
                display: flex; 
                align-items: center;
                color: white;
                max-width: 600px;
                margin-bottom: 3rem;
            ">
                <img src="{prof_image}" style="width: 100px; height: 100px; border-radius: 8px; object-fit: cover;"/>
                <div style="margin-left: 2rem;">
                    <h4 style="margin: 0;">{check_prof}</h4>
                    <p style="color: grey; font-size: 14px; margin-top: 2px;">{average_rating}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(f"### ✍ Reviews ({len(reviews)} Ratings)")
        for review in reversed(reviews):
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #ccc; 
                    border-radius: 10px; 
                    padding: 15px; 
                    background-color: #111; 
                    display: flex; 
                    color: white;
                    max-width: 700px;
                    margin-bottom: 20px;
                ">
                    <img src="{image_url}" style="width: 100px; height: 100px; border-radius: 8px; object-fit: cover; margin-right: 20px;"/>
                    <div>
                        <h4 style="margin: 1.5rem 0 4px;">Rating: {review['rating']} / 5.0 ⭐</h4>

                </div>
                """,
                unsafe_allow_html=True
            )

def rating():
    st.subheader("🤔 Share Your Feedback")
    

    with st.form("feedback_form"):
        feedback_title = st.text_input("Feedback Title")
        feedback_text = st.text_area("Write your feedback or suggestions")

        rating_options = {
            "⭐": 1,
            "⭐⭐": 2,
            "⭐⭐⭐": 3,
            "⭐⭐⭐⭐": 4,
            "⭐⭐⭐⭐⭐": 5
            
        }
        rating = st.selectbox("Rate your experience", list(rating_options.keys()))
        submit = st.form_submit_button("Submit Feedback")

        if submit:
            # Insert the feedback into the Supabase table
            supabase_data = storage.insert_data({
                "title": feedback_title,
                "description": feedback_text,
                "rating": rating_options[rating],
            }, "feedback")

            if supabase_data:
                
                st.balloons()
                st.success("Feedback submitted! Thanks you for your input.", icon="🎉")
            else:
                st.error("Failed to submit feedback")



def quantum_pdf():
    st.subheader("📚 Quantum PDFs")
    year_ops = {
        "1st Year": 1,
        "2nd Year": 2,
        "3rd Year": 3,
        "4th Year": 4
        
    }
    
    if (st.session_state.logged_in) and (st.session_state.role == "admin"):
        # Book upload form
        with st.form("upload_form"):
            title = st.text_input("Book Title")
            year = st.selectbox("Select Year", list(year_ops.keys()))
            
            cover_file = st.file_uploader("Upload Cover Image", type=["png", "jpg", "jpeg"])
            pdf_file = st.file_uploader("Upload PDF File", type=["pdf"])

            submit = st.form_submit_button("📤 Upload Book")

        # On form submit
        if submit:
            if not (title and cover_file and pdf_file):
                st.warning("Please fill all fields.")
            else:
                try:
                    # Upload cover to Supabase Storage
                    image_data = cover_file.read()
                    image_name = cover_file.name
                    image_file_name = storage.upload_file(image_data, image_name, "quantum_cover")
                    cover_url = storage.get_file_url(image_file_name, "quantum_cover")

                    # Upload PDF to Supabase Storage
                    pdf_data = pdf_file.read()
                    pdf_name = pdf_file.name
                    pdf_file_name = storage.upload_file(pdf_data, pdf_name, "quantum_pdf")
                    pdf_url = storage.get_file_url(pdf_file_name, "quantum_pdf")



                    # Insert into Supabase table
                    data = {
                        "title": title,
                        "cover": cover_url,
                        "pdf_url": pdf_url,
                        "year": year_ops[year]
                    }
                    
                    storage.insert_data(data, "quantum_books")

                    st.success("✅ Book uploaded successfully!")
                    st.image(cover_url, caption="Uploaded Cover", width=300)

                except Exception as e:
                    st.error(f"❌ Error uploading book: {e}")
        
        st.markdown("---")

    quantum_books = storage.get_data("quantum_books")
    
    
    year = st.selectbox("Select Year", list(year_ops.keys()))
    st.markdown("---")
    
    if year:
        quantum_books = [x for x in quantum_books if x['year'] == year_ops[year]]

        if quantum_books:
            # Display books in a 4-column grid
            cols = st.columns(4)

            for idx, book in enumerate(quantum_books):
                col = cols[idx % 4]
                with col:
                    st.image(book["cover"], width=300)
                    st.markdown(f"**{book['title']}**", unsafe_allow_html=True)

                    if book["pdf_url"]:
                        res = requests.get(book['pdf_url'])
                        if res.status_code == 200:
                            pdf_data = res.content
                            st.download_button(
                                label="📄 Download PDF",
                                data=pdf_data,
                                file_name=f"{book['title']}_quantum.pdf",
                                mime="application/pdf",
                                key=f"download-button-{book['title']}-{book['id']}"
                            )
                        else:
                            st.error("Failed to retrieve PDF!")

                    # Delete button
                    if (st.session_state.logged_in ==True) and (st.session_state.role == "admin"):
                        delete_button = st.button(f"🚮 Delete Quantum", key=f"delete-button-{book['id']}")
                        if delete_button:
                            if storage.delete_record(table_name="quantum_books", column="id", value=book["id"]):
                                st.success("Quantum deleted successfully!", icon="🎉")
                            else:
                                st.error("Failed to delete quantum!", icon="❌")

                # Create new row every 4 quantum_books
                if (idx + 1) % 4 == 0 and (idx + 1) != len(quantum_books):
                    st.markdown("---")
                    cols = st.columns(4)
        else:
            st.error("No quantum books available")


# ------------------------------------- MAIN ----------------------------------------


st.set_page_config(
    page_title="Cigarette Society",  # The title that appears in the browser tab
    page_icon=":space_invader:",  # Optional: You can use emojis or upload an image as the icon
    layout="wide"  # Optional: 'centered' or 'wide' layout
)


IST_OFFSET = datetime.timedelta(hours=5, minutes=30)
IST = datetime.timezone(IST_OFFSET)

def format_timestamp(timestamp_str):
    # Parse ISO timestamp
    utc_time = parser.isoparse(timestamp_str)

    # Convert to IST
    ist_time = utc_time.astimezone(IST)

    # Format it nicely
    return ist_time.strftime("%B %d, %Y – %I:%M %p IST")


components.html(ga_code, height=0)


storage = SupabaseStorage(st.secrets['SUPABASE_URL'], st.secrets['SUPABASE_KEY'])
st.title("👾 Cigarette Society")


with st.sidebar:
    
    st.image("https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExMWV5c2RiZmM2ajk5Nmd5ejdoOHZvb3BwZ2I2anMzaXlwMGNybzZ3aSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ukwPlCmJ5RmlqvQCpA/giphy.gif", width=150)
    st.markdown("## 🎓 Cigarette Society")
    st.markdown("---")

    menu = st.radio(
        "Choose Section",
        ["🏠 Home", "🔐 Admin Login", "📝 Solved Assignments", "📒 Notes", "📘 Sessional PYQs", "📚 Quantum PDF", "🤩 Rate your professors", "📢 Announcements", "🌟 Rate Us"],
        label_visibility="collapsed"
    )


    st.markdown("---")

    color_ops = ['blue', 'red', 'violet', 'green', 'rainbow']
    
    st.markdown(f"Made with ❤️ by :{random.choice(color_ops)}[Madhav]")
    spotify_markdown = """[![spotify-github-profile](https://spotify-github-profile.kittinanx.com/api/view?uid=31lagegr4yfxqaskpwdn77jrqbci&cover_image=true&theme=default&show_offline=false&background_color=121212&interchange=true)](https://spotify-github-profile.kittinanx.com/api/view?uid=31lagegr4yfxqaskpwdn77jrqbci&redirect=true)"""
    st.markdown(spotify_markdown)
    


if menu == "🔐 Admin Login":
    login()

# ---------------- HOME ----------------
elif menu == "🏠 Home":
    home()

# ---------------- ASSIGNMENTS ----------------
elif menu == "📝 Solved Assignments":
    assignments()

# ---------------- NOTES ----------------
elif menu == "📒 Notes":
    notes()

# ---------------- PYQs ----------------
elif menu == "📘 Sessional PYQs":
    sess_pyqs()
    
# ---------------- ANNOUNCEMENTS ----------------
elif menu == "📢 Announcements":
    announcements()


# ---------------- FEEDBACK FORM ----------------
elif menu == "🤩 Rate your professors":
    feedback_form()
    
# ---------------- RATE US ----------------
elif menu == "🌟 Rate Us":
    rating()


elif menu == "📚 Quantum PDF":
    quantum_pdf()

else:
    login()

