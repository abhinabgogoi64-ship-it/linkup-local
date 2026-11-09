
import streamlit as st
from urllib.parse import urlparse
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from supabase import create_client


# ============================================================
# 1. CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="LinkUp Local",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SUPABASE_URL = "https://xgqhbvrfsgqhkegkchwc.supabase.co"

try:
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"].strip()

    if not SUPABASE_KEY:
        st.error("Supabase key is empty. Check secrets.toml.")
        st.stop()

    if SUPABASE_KEY.startswith("sb_secret_"):
        st.error(
            "A secret key cannot be used in this application. "
            "Use your Supabase publishable key instead."
        )
        st.stop()

except KeyError:
    st.error("Supabase key is missing. Check secrets.toml.")
    st.stop()

except Exception as e:
    st.error(f"Could not load Supabase configuration: {e}")
    st.stop()


def new_supabase_client():
    return create_client(
        SUPABASE_URL.rstrip("/"),
        SUPABASE_KEY
    )


try:
    if "supabase_client" not in st.session_state:
        st.session_state.supabase_client = new_supabase_client()

    supabase = st.session_state.supabase_client

except Exception as e:
    st.error(f"Supabase initialization failed: {e}")
    st.stop()


# ============================================================
# 2. DESIGN
# ============================================================

st.markdown("""
<style>
.stApp {
    background: #FFFFFF;
    color: #171717;
}

.block-container {
    max-width: 1050px;
    padding: 1.5rem 1rem 3rem 1rem;
}

h1, h2, h3, h4 {
    color: #171717 !important;
}

p, label, li {
    color: #333333 !important;
}

[data-testid="stWidgetLabel"] p {
    color: #222222 !important;
}

[data-testid="stMarkdownContainer"] p {
    color: #333333;
}

/* INPUT FIELDS */

div[data-baseweb="input"],
div[data-baseweb="textarea"] {
    background: #FFFFFF !important;
    border: 1px solid #D5D5D5 !important;
    border-radius: 9px !important;
}

input, textarea {
    color: #171717 !important;
    -webkit-text-fill-color: #171717 !important;
    caret-color: #171717 !important;
    background-color: #FFFFFF !important;
}

input::placeholder,
textarea::placeholder {
    color: #888888 !important;
    -webkit-text-fill-color: #888888 !important;
}

/* CHROME AUTOFILL FIX */

input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus,
input:-webkit-autofill:active,
textarea:-webkit-autofill,
textarea:-webkit-autofill:hover,
textarea:-webkit-autofill:focus,
textarea:-webkit-autofill:active {
    -webkit-box-shadow: 0 0 0 1000px #FFFFFF inset !important;
    box-shadow: 0 0 0 1000px #FFFFFF inset !important;
    -webkit-text-fill-color: #171717 !important;
    caret-color: #171717 !important;
    transition: background-color 9999s ease-in-out 0s !important;
}

div[data-baseweb="input"] > div {
    background-color: #FFFFFF !important;
}

div[data-baseweb="input"] input {
    background-color: transparent !important;
    color: #171717 !important;
    -webkit-text-fill-color: #171717 !important;
}

/* SELECT BOXES */

div[data-baseweb="select"] * {
    color: #171717 !important;
}

/* SIDEBAR */

[data-testid="stSidebar"] {
    background: #252525;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

/* TABS */

button[data-baseweb="tab"] {
    color: #555555 !important;
    font-weight: 600;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #1265E8 !important;
    border-bottom-color: #1265E8 !important;
}

/* BUTTONS */

div.stButton > button,
div.stFormSubmitButton > button,
a[data-testid="stLinkButton"] {
    background: #1265E8 !important;
    color: #FFFFFF !important;
    border: 1px solid #1265E8 !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    min-height: 42px;
}

div.stButton > button *,
div.stFormSubmitButton > button * {
    color: #FFFFFF !important;
}

div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    background: #084EBB !important;
}

/* CONTAINERS */

div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #E5E5E5;
    border-radius: 12px;
}

[data-testid="stCaptionContainer"] p {
    color: #777777 !important;
}

hr {
    border-color: #E5E5E5 !important;
}

[data-testid="stMetricValue"] {
    color: #171717 !important;
}

/* MOBILE */

@media (max-width: 640px) {
    .block-container {
        padding: 1rem 0.8rem 2rem 0.8rem;
    }

    h1 {
        font-size: 1.8rem !important;
    }

    h2 {
        font-size: 1.4rem !important;
    }

    div.stButton > button,
    div.stFormSubmitButton > button {
        width: 100%;
    }
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. SESSION MANAGEMENT
# ============================================================

DEFAULTS = {
    "access_token": None,
    "refresh_token": None,
    "user_id": None,
    "user_email": None,
    "recovery_mode": False,
    "confirm_profile_delete": False,
    "discovery_matches": None,
    "discovery_error": None
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def clear_session():
    for key in DEFAULTS:
        st.session_state[key] = DEFAULTS[key]

    st.session_state.supabase_client = new_supabase_client()


def save_session(response):
    session = getattr(response, "session", None)
    user = getattr(response, "user", None)

    if not session or not user:
        return False

    st.session_state.access_token = session.access_token
    st.session_state.refresh_token = session.refresh_token
    st.session_state.user_id = user.id
    st.session_state.user_email = user.email

    return True


def restore_session():
    access_token = st.session_state.access_token
    refresh_token = st.session_state.refresh_token

    if not access_token or not refresh_token:
        return None

    try:
        response = supabase.auth.set_session(
            access_token,
            refresh_token
        )

        if not response.session:
            clear_session()
            return None

        st.session_state.access_token = response.session.access_token
        st.session_state.refresh_token = response.session.refresh_token

        user_response = supabase.auth.get_user(
            st.session_state.access_token
        )

        user = user_response.user

        if user:
            st.session_state.user_id = user.id
            st.session_state.user_email = user.email
            return user

    except Exception:
        clear_session()

    return None


def show_auth_error(action, error):
    st.error(f"{action} failed: {str(error)}")
    st.caption(
        "Check your Supabase project configuration "
        "and Authentication logs."
    )


# ============================================================
# 4. PASSWORD RECOVERY
# ============================================================

def process_recovery_link():
    token_hash = st.query_params.get("token_hash")
    token_type = st.query_params.get("type")

    if token_hash and token_type == "recovery":
        try:
            response = supabase.auth.verify_otp({
                "token_hash": token_hash,
                "type": "recovery"
            })

            if save_session(response):
                st.session_state.recovery_mode = True
                st.query_params.clear()
                st.rerun()
            else:
                st.error(
                    "Recovery verification did not create a session. "
                    "Request a new recovery email."
                )

        except Exception as e:
            show_auth_error("Recovery verification", e)


process_recovery_link()


# ============================================================
# 5. AUTHENTICATION SCREEN
# ============================================================

def authentication_screen():

    st.markdown("# 📍 LinkUp Local")
    st.markdown("### Find your people.")
    st.caption(
        "Discover people nearby. Connect through shared interests."
    )
    st.divider()

    login_tab, signup_tab, recovery_tab = st.tabs([
        "Log in",
        "Create account",
        "Forgot password"
    ])

    # LOGIN

    with login_tab:
        st.subheader("Welcome back")

        with st.form("login_form"):

            email = st.text_input("Email address")
            password = st.text_input(
                "Password",
                type="password"
            )

            login_button = st.form_submit_button(
                "Log in",
                use_container_width=True
            )

        if login_button:

            if not email.strip() or not password:
                st.error("Please enter your email and password.")

            else:
                try:
                    response = supabase.auth.sign_in_with_password({
                        "email": email.strip(),
                        "password": password
                    })

                    if save_session(response):
                        st.success("Login successful.")
                        st.rerun()

                    else:
                        st.error(
                            "Login returned no valid session. "
                            "Check whether your email is verified."
                        )

                except Exception as e:
                    show_auth_error("Login", e)

    # SIGN UP

    with signup_tab:
        st.subheader("Create your account")

        with st.form("signup_form"):

            signup_email = st.text_input(
                "Email address",
                key="signup_email"
            )

            signup_password = st.text_input(
                "Password",
                type="password",
                key="signup_password"
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                key="confirm_signup_password"
            )

            signup_button = st.form_submit_button(
                "Create account",
                use_container_width=True
            )

        if signup_button:

            if not signup_email.strip():
                st.error("Please enter your email address.")

            elif len(signup_password) < 8:
                st.error(
                    "Use a password with at least 8 characters."
                )

            elif signup_password != confirm_password:
                st.error("Your passwords do not match.")

            else:
                try:
                    response = supabase.auth.sign_up({
                        "email": signup_email.strip(),
                        "password": signup_password
                    })

                    if save_session(response):
                        st.success("Account created successfully.")
                        st.rerun()

                    else:
                        st.success(
                            "Registration submitted. Please check "
                            "your email and verify your account "
                            "before logging in."
                        )

                except Exception as e:
                    show_auth_error("Registration", e)

    # PASSWORD RECOVERY

    with recovery_tab:
        st.subheader("Reset your password")

        with st.form("recovery_form"):

            recovery_email = st.text_input(
                "Registered email address"
            )

            recovery_button = st.form_submit_button(
                "Send recovery email",
                use_container_width=True
            )

        if recovery_button:

            if not recovery_email.strip():
                st.error("Enter your registered email address.")

            else:
                try:
                    supabase.auth.reset_password_for_email(
                        recovery_email.strip()
                    )

                    st.success(
                        "If the account exists, a recovery email "
                        "has been requested. Check your inbox "
                        "and spam folder."
                    )

                except Exception as e:
                    show_auth_error("Password recovery", e)

    st.divider()
    st.caption(
        "Use LinkUp Local respectfully and responsibly."
    )


# ============================================================
# 6. PASSWORD UPDATE SCREEN
# ============================================================

def password_update_screen():

    st.markdown("# 📍 LinkUp Local")
    st.subheader("Choose a new password")

    st.info(
        "Your recovery link has been verified. "
        "Enter your new password below."
    )

    with st.form("new_password_form"):

        new_password = st.text_input(
            "New password",
            type="password"
        )

        confirm_new_password = st.text_input(
            "Confirm new password",
            type="password"
        )

        update_button = st.form_submit_button(
            "Update password",
            use_container_width=True
        )

    if update_button:

        if len(new_password) < 8:
            st.error(
                "Your password must contain at least 8 characters."
            )

        elif new_password != confirm_new_password:
            st.error("Your passwords do not match.")

        else:
            try:
                supabase.auth.update_user({
                    "password": new_password
                })

                clear_session()

                st.success(
                    "Password updated successfully. "
                    "Please log in using your new password."
                )
                st.rerun()

            except Exception as e:
                show_auth_error("Password update", e)


# ============================================================
# 7. AUTHENTICATION ROUTING
# ============================================================

current_user = restore_session()

if st.session_state.recovery_mode:
    password_update_screen()
    st.stop()

if current_user is None:
    authentication_screen()
    st.stop()


# ============================================================
# 8. LOCATION ENGINE
# ============================================================

@st.cache_data(ttl=86400)
def get_coordinates(location_name):

    try:
        geolocator = Nominatim(
            user_agent="linkup_local_v3",
            timeout=10
        )

        location = geolocator.geocode(location_name)

        if location:
            return location.latitude, location.longitude

        return None, None

    except (GeocoderTimedOut, GeocoderUnavailable):
        return None, None

    except Exception:
        return None, None


# ============================================================
# 9. DATABASE FUNCTIONS
# ============================================================

USER_ID = current_user.id

SAFE_PROFILE_COLUMNS = (
    "id,user_id,name,city_display,goal,"
    "chat_link,is_active,created_at,updated_at"
)


def get_my_profile():

    response = (
        supabase.table("profiles")
        .select(SAFE_PROFILE_COLUMNS)
        .eq("user_id", USER_ID)
        .limit(1)
        .execute()
    )

    return response.data[0] if response.data else None


def create_or_update_profile(profile_data, existing_profile):

    if existing_profile:

        return (
            supabase.table("profiles")
            .update(profile_data)
            .eq("user_id", USER_ID)
            .execute()
        )

    profile_data["user_id"] = USER_ID

    return (
        supabase.table("profiles")
        .insert(profile_data)
        .execute()
    )


def delete_my_profile():

    return (
        supabase.table("profiles")
        .delete()
        .eq("user_id", USER_ID)
        .execute()
    )


def discover_people(radius):

    response = supabase.rpc(
        "discover_profiles",
        {"p_radius_km": int(radius)}
    ).execute()

    return response.data or []


def block_user(blocked_user_id):

    return supabase.table("user_blocks").insert({
        "blocker_id": USER_ID,
        "blocked_id": blocked_user_id
    }).execute()


def unblock_user(blocked_user_id):

    return (
        supabase.table("user_blocks")
        .delete()
        .eq("blocker_id", USER_ID)
        .eq("blocked_id", blocked_user_id)
        .execute()
    )


def report_user(reported_user_id, reason, details):

    return supabase.table("user_reports").insert({
        "reporter_id": USER_ID,
        "reported_id": reported_user_id,
        "reason": reason,
        "details": details.strip()
    }).execute()


def get_blocked_users():

    response = (
        supabase.table("user_blocks")
        .select("blocked_id,created_at")
        .eq("blocker_id", USER_ID)
        .execute()
    )

    return response.data or []


# ============================================================
# 10. CHAT DATABASE FUNCTIONS
# ============================================================

def get_profile_for_user(user_id):

    try:
        response = (
            supabase.table("profiles")
            .select("user_id,name,city_display,goal")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        return response.data[0] if response.data else None

    except Exception:
        return None


def send_chat_request(recipient_id):

    if recipient_id == USER_ID:
        raise ValueError("You cannot send a request to yourself.")

    # Check existing outgoing request.

    outgoing = (
        supabase.table("chat_requests")
        .select("id,status")
        .eq("sender_id", USER_ID)
        .eq("recipient_id", recipient_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if outgoing.data:

        status = outgoing.data[0]["status"]

        if status == "pending":
            return "You have already sent a request to this person."

        if status == "accepted":
            return "You are already connected. Open the Chat tab."

    # Check incoming request.

    incoming = (
        supabase.table("chat_requests")
        .select("id,status")
        .eq("sender_id", recipient_id)
        .eq("recipient_id", USER_ID)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if incoming.data:

        status = incoming.data[0]["status"]

        if status == "pending":
            return (
                "This person has already sent you a request. "
                "Open the Chat tab to respond."
            )

        if status == "accepted":
            return "You are already connected. Open the Chat tab."

    # Send new request.

    supabase.table("chat_requests").insert({
        "sender_id": USER_ID,
        "recipient_id": recipient_id
    }).execute()

    return "Chat request sent successfully!"


def get_incoming_chat_requests():

    response = (
        supabase.table("chat_requests")
        .select("id,sender_id,created_at,status")
        .eq("recipient_id", USER_ID)
        .eq("status", "pending")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data or []


def respond_to_chat_request(request_id, accept):

    response = supabase.rpc(
        "respond_to_chat_request",
        {
            "p_request_id": request_id,
            "p_accept": accept
        }
    ).execute()

    return response.data


def get_my_conversations():

    response = (
        supabase.table("conversation_members")
        .select("conversation_id")
        .eq("user_id", USER_ID)
        .execute()
    )

    conversations = []

    for item in response.data or []:

        conversation_id = item["conversation_id"]

        members_response = (
            supabase.table("conversation_members")
            .select("user_id")
            .eq("conversation_id", conversation_id)
            .execute()
        )

        members = members_response.data or []

        other_members = [
            member["user_id"]
            for member in members
            if member["user_id"] != USER_ID
        ]

        if not other_members:
            continue

        other_user_id = other_members[0]
        profile = get_profile_for_user(other_user_id)

        if profile:
            display_name = profile["name"]
            city = profile.get("city_display", "")
        else:
            display_name = "LinkUp user"
            city = ""

        label = display_name

        if city:
            label += f" · {city}"

        conversations.append({
            "conversation_id": conversation_id,
            "other_user_id": other_user_id,
            "label": label
        })

    return conversations


def get_messages(conversation_id):

    response = (
        supabase.table("messages")
        .select("id,sender_id,body,created_at")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    )

    return response.data or []


def send_message(conversation_id, body):

    clean_body = body.strip()

    if not clean_body:
        raise ValueError("Please enter a message.")

    if len(clean_body) > 5000:
        raise ValueError("Messages cannot exceed 5,000 characters.")

    return (
        supabase.table("messages")
        .insert({
            "conversation_id": conversation_id,
            "sender_id": USER_ID,
            "body": clean_body
        })
        .execute()
    )


# ============================================================
# 11. VALIDATION
# ============================================================

def valid_chat_link(link):

    if not link:
        return True

    parsed = urlparse(link)

    return (
        parsed.scheme in ["http", "https"]
        and bool(parsed.netloc)
    )


def valid_profile_text(value, max_length):

    return (
        bool(value.strip())
        and len(value.strip()) <= max_length
    )


# ============================================================
# 12. HEADER
# ============================================================

st.markdown("# 📍 LinkUp Local")
st.markdown("### Find your people.")
st.caption(
    "Discover people nearby. Connect through shared interests."
)
st.caption(f"Logged in as {current_user.email}")
st.divider()


# ============================================================
# 13. LOAD PROFILE
# ============================================================

try:
    my_profile = get_my_profile()

except Exception as e:
    show_auth_error("Profile loading", e)
    st.stop()


# ============================================================
# 14. MAIN TABS
# ============================================================

tab_discover, tab_chat, tab_profile, tab_safety, tab_account = st.tabs([
    "🔍 Discover",
    "💬 Chat",
    "👤 My Profile" if my_profile else "➕ Create Profile",
    "🛡️ Safety",
    "⚙️ Account"
])


# ============================================================
# TAB 1 — DISCOVER
# ============================================================

with tab_discover:

    st.subheader("Discover people around you")

    if not my_profile:

        st.info(
            "Create your profile first to discover people nearby."
        )

    else:

        st.caption(
            f"Your discovery location: {my_profile['city_display']}"
        )

        radius = st.slider(
            "Search radius (km)",
            min_value=5,
            max_value=500,
            value=25,
            step=5,
            key="discovery_radius"
        )

        if st.button(
            "Find people",
            use_container_width=True
        ):

            with st.spinner("Discovering people nearby..."):

                try:
                    st.session_state.discovery_matches = (
                        discover_people(radius)
                    )

                    st.session_state.discovery_error = None

                except Exception as e:
                    st.session_state.discovery_error = str(e)

        if st.session_state.discovery_error:

            st.error(
                f"Discovery failed: "
                f"{st.session_state.discovery_error}"
            )

        matches = st.session_state.discovery_matches

        if matches is not None:

            st.divider()

            st.subheader(
                f"{len(matches)} people discovered"
            )

            if not matches:

                st.info(
                    "No profiles found. "
                    "Try increasing your search radius."
                )

            for person in matches:

                with st.container(border=True):

                    st.markdown(f"### {person['name']}")

                    st.caption(
                        f"📍 {person['city_display']}"
                    )

                    st.markdown(
                        f"**Interested in:** {person['goal']}"
                    )

                    distance = person.get(
                        "approximate_distance_km"
                    )

                    if distance is not None:

                        st.metric(
                            "Approximate distance",
                            f"~{distance} km"
                        )

                    else:
                        st.caption(
                            "Approximate distance unavailable."
                        )

                    # IN-APP CHAT REQUEST

                    if st.button(
                        "💬 Send chat request",
                        key=f"chat_request_{person['user_id']}",
                        use_container_width=True
                    ):

                        try:

                            result = send_chat_request(
                                person["user_id"]
                            )

                            if "successfully" in result:
                                st.success(result)
                            else:
                                st.info(result)

                        except Exception as e:
                            show_auth_error(
                                "Sending chat request", e
                            )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "Block user",
                            key=f"block_{person['user_id']}",
                            use_container_width=True
                        ):

                            try:
                                block_user(person["user_id"])

                                st.session_state.discovery_matches = None

                                st.success("User blocked.")
                                st.rerun()

                            except Exception as e:
                                show_auth_error(
                                    "Blocking user", e
                                )

                    with col2:

                        with st.popover(
                            "Report user",
                            use_container_width=True
                        ):

                            with st.form(
                                f"report_form_{person['user_id']}"
                            ):

                                reason = st.selectbox(
                                    "Reason",
                                    [
                                        "Spam",
                                        "Fake profile",
                                        "Harassment",
                                        "Inappropriate content",
                                        "Suspicious activity",
                                        "Other"
                                    ]
                                )

                                details = st.text_area(
                                    "Additional details (optional)"
                                )

                                submit_report = st.form_submit_button(
                                    "Submit report",
                                    use_container_width=True
                                )

                            if submit_report:

                                try:

                                    report_user(
                                        person["user_id"],
                                        reason,
                                        details
                                    )

                                    st.success(
                                        "Your report has been submitted."
                                    )

                                except Exception as e:
                                    show_auth_error(
                                        "Report submission", e
                                    )


# ============================================================
# TAB 2 — CHAT
# ============================================================

with tab_chat:

    st.subheader("Your conversations")

    st.caption(
        "Send a request, connect with someone, "
        "and start a private conversation."
    )

    if st.button(
        "🔄 Refresh chats",
        key="refresh_chats"
    ):
        st.rerun()

    st.divider()

    # --------------------------------------------------------
    # INCOMING REQUESTS
    # --------------------------------------------------------

    st.markdown("### 📩 Incoming requests")

    try:

        incoming_requests = get_incoming_chat_requests()

        if not incoming_requests:

            st.info("You don't have any pending chat requests.")

        else:

            for request in incoming_requests:

                request_id = request["id"]
                sender_id = request["sender_id"]

                sender_profile = get_profile_for_user(sender_id)

                if sender_profile:
                    sender_name = sender_profile["name"]
                    sender_city = sender_profile.get(
                        "city_display", ""
                    )
                else:
                    sender_name = "LinkUp user"
                    sender_city = ""

                with st.container(border=True):

                    st.markdown(f"**{sender_name}**")

                    if sender_city:
                        st.caption(f"📍 {sender_city}")

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "Accept",
                            key=f"accept_{request_id}",
                            use_container_width=True
                        ):

                            try:

                                respond_to_chat_request(
                                    request_id,
                                    True
                                )

                                st.success(
                                    f"You are now connected with {sender_name}."
                                )

                                st.rerun()

                            except Exception as e:
                                show_auth_error(
                                    "Accepting chat request", e
                                )

                    with col2:

                        if st.button(
                            "Decline",
                            key=f"decline_{request_id}",
                            use_container_width=True
                        ):

                            try:

                                respond_to_chat_request(
                                    request_id,
                                    False
                                )

                                st.success("Request declined.")
                                st.rerun()

                            except Exception as e:
                                show_auth_error(
                                    "Declining chat request", e
                                )

    except Exception as e:

        show_auth_error(
            "Loading incoming requests", e
        )

    st.divider()

    # --------------------------------------------------------
    # ACCEPTED CONVERSATIONS
    # --------------------------------------------------------

    st.markdown("### 💬 My chats")

    try:

        conversations = get_my_conversations()

        if not conversations:

            st.info(
                "You don't have any conversations yet. "
                "Visit Discover and send someone a chat request."
            )

        else:

            conversation_labels = [
                conversation["label"]
                for conversation in conversations
            ]

            selected_label = st.selectbox(
                "Choose a conversation",
                conversation_labels,
                key="selected_conversation"
            )

            selected_index = conversation_labels.index(
                selected_label
            )

            selected_conversation = conversations[selected_index]

            conversation_id = selected_conversation[
                "conversation_id"
            ]

            st.divider()

            st.markdown(
                f"### {selected_conversation['label']}"
            )

            # LOAD MESSAGE HISTORY

            try:

                messages = get_messages(conversation_id)

                if not messages:

                    st.info(
                        "This conversation is ready. "
                        "Send the first message!"
                    )

                else:

                    for message in messages:

                        is_my_message = (
                            message["sender_id"] == USER_ID
                        )

                        with st.chat_message(
                            "user" if is_my_message else "assistant"
                        ):

                            st.markdown(message["body"])

                            st.caption(
                                "You" if is_my_message
                                else selected_conversation["label"]
                            )

            except Exception as e:

                show_auth_error(
                    "Loading messages", e
                )

            st.divider()

            # SEND MESSAGE

            with st.form(
                f"message_form_{conversation_id}",
                clear_on_submit=True
            ):

                message_text = st.text_area(
                    "Your message",
                    placeholder="Write something...",
                    max_chars=5000,
                    height=100
                )

                send_button = st.form_submit_button(
                    "Send message",
                    use_container_width=True
                )

            if send_button:

                if not message_text.strip():

                    st.warning("Please enter a message.")

                else:

                    try:

                        send_message(
                            conversation_id,
                            message_text
                        )

                        st.rerun()

                    except Exception as e:

                        show_auth_error(
                            "Sending message", e
                        )

    except Exception as e:

        show_auth_error(
            "Loading conversations", e
        )


# ============================================================
# TAB 3 — PROFILE
# ============================================================

with tab_profile:

    st.subheader(
        "Edit your profile" if my_profile
        else "Create your LinkUp profile"
    )

    st.caption(
        "Use your city or locality, not your home address."
    )

    with st.form("profile_form"):

        name = st.text_input(
            "Your name / handle",
            value=my_profile["name"] if my_profile else "",
            placeholder="e.g. Abhinab"
        )

        locality = st.text_input(
            "Your city or locality",
            value=my_profile["city_display"] if my_profile else "",
            placeholder="e.g. Dibrugarh, Assam"
        )

        goal = st.text_input(
            "What are you interested in?",
            value=my_profile["goal"] if my_profile else "",
            placeholder="e.g. Tennis, Coding, Hiking..."
        )

        chat_link = st.text_input(
            "Group chat link (optional)",
            value=my_profile["chat_link"] if my_profile else "",
            placeholder="https://..."
        )

        save_button = st.form_submit_button(
            "Save profile",
            use_container_width=True
        )

    if save_button:

        if not valid_profile_text(name, 60):

            st.error(
                "Enter a name (maximum 60 characters)."
            )

        elif not valid_profile_text(locality, 120):

            st.error("Enter your city or locality.")

        elif not valid_profile_text(goal, 200):

            st.error(
                "Tell people what you are interested in."
            )

        elif not valid_chat_link(chat_link.strip()):

            st.error(
                "Please enter a valid HTTP or HTTPS link."
            )

        else:

            with st.spinner("Verifying your locality..."):

                latitude, longitude = get_coordinates(
                    locality.strip()
                )

            if latitude is None or longitude is None:

                st.error(
                    "We couldn't verify your locality. "
                    "Try including your city and state."
                )

            else:

                profile_data = {
                    "name": name.strip(),
                    "city_display": locality.strip(),
                    "latitude": latitude,
                    "longitude": longitude,
                    "goal": goal.strip(),
                    "chat_link": chat_link.strip(),
                    "is_active": True
                }

                try:

                    create_or_update_profile(
                        profile_data,
                        my_profile
                    )

                    st.session_state.discovery_matches = None

                    st.success(
                        "Your profile has been saved successfully!"
                    )

                    st.rerun()

                except Exception as e:
                    show_auth_error(
                        "Profile saving", e
                    )

    if my_profile:

        st.divider()
        st.subheader("Delete profile")

        st.caption(
            "This removes your LinkUp profile, "
            "not your login account."
        )

        if not st.session_state.confirm_profile_delete:

            if st.button(
                "Delete my profile",
                use_container_width=True
            ):

                st.session_state.confirm_profile_delete = True
                st.rerun()

        else:

            st.warning(
                "Are you sure? Your profile will no longer "
                "appear in discovery."
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "Yes, delete",
                    use_container_width=True
                ):

                    try:

                        delete_my_profile()

                        st.session_state.confirm_profile_delete = False
                        st.session_state.discovery_matches = None

                        st.success("Profile deleted.")
                        st.rerun()

                    except Exception as e:
                        show_auth_error(
                            "Profile deletion", e
                        )

            with col2:

                if st.button(
                    "Cancel",
                    use_container_width=True
                ):

                    st.session_state.confirm_profile_delete = False
                    st.rerun()


# ============================================================
# TAB 4 — SAFETY
# ============================================================

with tab_safety:

    st.subheader("Your safety")

    st.caption(
        "Manage the users you have blocked."
    )

    try:

        blocked_users = get_blocked_users()

        if not blocked_users:

            st.info("You haven't blocked anyone.")

        else:

            st.markdown(
                f"**Blocked accounts: {len(blocked_users)}**"
            )

            for blocked in blocked_users:

                blocked_id = blocked["blocked_id"]

                with st.container(border=True):

                    st.caption(
                        f"Account ID: {blocked_id}"
                    )

                    if st.button(
                        "Unblock",
                        key=f"unblock_{blocked_id}",
                        use_container_width=True
                    ):

                        try:

                            unblock_user(blocked_id)

                            st.success("User unblocked.")
                            st.rerun()

                        except Exception as e:
                            show_auth_error(
                                "Unblocking user", e
                            )

    except Exception as e:
        show_auth_error(
            "Blocked-user loading", e
        )

    st.divider()

    st.markdown("### Community guidelines")

    st.markdown("""
    - Respect other users.
    - Do not share private information.
    - Never share your home address publicly.
    - Report suspicious or inappropriate behaviour.
    - Meet new people in safe, public locations.
    """)


# ============================================================
# TAB 5 — ACCOUNT
# ============================================================

with tab_account:

    st.subheader("Account settings")

    st.markdown(
        f"**Email:** {current_user.email}"
    )

    st.caption(
        "Your account is protected by Supabase authentication."
    )

    st.divider()

    st.markdown("### Sign out")

    if st.button(
        "Log out",
        use_container_width=True
    ):

        try:
            supabase.auth.sign_out()

        except Exception:
            pass

        clear_session()
        st.rerun()

    st.divider()

    st.markdown("### Permanent account deletion")

    st.info(
        "Permanent deletion is not enabled yet. "
        "We will add it through a secure Supabase Edge Function "
        "so your account and associated data can be deleted safely."
    )

    st.markdown("### Report moderation")

    st.info(
        "Admin report review will be added through a secure backend. "
        "Reports will not be exposed to ordinary users."
    )


# ============================================================
# 15. FOOTER
# ============================================================

st.divider()

st.markdown("""
<div style="
    text-align:center;
    color:#888888;
    font-size:13px;
    padding:10px;
">
    LinkUp Local · Find your people. Wherever you are.
</div>
""", unsafe_allow_html=True)
s