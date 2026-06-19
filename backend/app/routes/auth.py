import httpx
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse

from app.auth.jwt import create_access_token, get_current_user
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# ── GitHub OAuth Constants ────────────────────────────────────────────────────
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


# ── GitHub OAuth Helpers ──────────────────────────────────────────────────────

def get_github_login_url() -> str:
    """Build the GitHub OAuth redirect URL."""
    return (
        f"{GITHUB_AUTHORIZE_URL}"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&scope=read:user"
    )


async def exchange_code_for_token(code: str) -> str:
    """Exchange the authorization code for a GitHub access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
        )
    data = response.json()
    access_token = data.get("access_token")
    if not access_token:
        raise ValueError(f"GitHub did not return an access token: {data}")
    return access_token


async def get_github_user(access_token: str) -> dict:
    """Fetch the authenticated user's GitHub profile."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
    return response.json()


# ── Auth Endpoints ────────────────────────────────────────────────────────────

@router.get("/login")
def login():
    """
    Redirect the user to GitHub's OAuth login page.
    The frontend calls this when the user clicks 'Login with GitHub'.
    """
    return RedirectResponse(url=get_github_login_url())


@router.get("/callback")
async def callback(code: str):
    """
    GitHub redirects here after the user approves the OAuth app.
    We exchange the short-lived GitHub code for a long-lived JWT token.
    """
    try:
        # Step 1: Exchange the code for a GitHub access token (short-lived)
        github_token = await exchange_code_for_token(code)

        # Step 2: Fetch the user's GitHub profile using the GitHub token
        github_user = await get_github_user(github_token)

        username = github_user.get("login")
        avatar_url = github_user.get("avatar_url", "")
        name = github_user.get("name") or username

        if not username:
            raise HTTPException(status_code=400, detail="Could not fetch GitHub username")

        # Step 3: Exchange the GitHub token for our own long-lived JWT token
        jwt_token = create_access_token(
            github_username=username,
            avatar_url=avatar_url,
            name=name,
        )

        # DEV MODE: Return JSON so we can test without the frontend
        # TODO: Switch back to RedirectResponse when frontend is ready:
        # return RedirectResponse(url=f"{settings.FRONTEND_URL}/auth/callback?token={jwt_token}")
        return {
            "token": jwt_token,
            "username": username,
            "name": name,
            "avatar_url": avatar_url,
            "is_admin": username == settings.ADMIN_GITHUB_USERNAME,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    """
    Returns the currently logged-in user's profile.
    The frontend calls this on load to check if the user is still logged in.
    """
    return {
        "username": current_user["sub"],
        "name": current_user["name"],
        "avatar_url": current_user["avatar_url"],
        "is_admin": current_user["is_admin"],
    }
