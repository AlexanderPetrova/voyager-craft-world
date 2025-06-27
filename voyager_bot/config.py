import os
from dotenv import load_dotenv

getenv = load_dotenv()

PRIVATE_KEY_FILE = os.getenv('PRIVATE_KEY_FILE', 'private_key.txt')
PROXY_FILE = os.getenv('PROXY_FILE', 'proxies.txt')
USE_PROXY = os.getenv('USE_PROXY', 'false').lower() == 'true'
SESSION_DIR = os.getenv('SESSION_DIR', 'sessions') 
OPEN_STURDY_CHEESE = int(os.getenv('OPEN_STURDY_CHEESE', 10))

try:
    DELAY_BETWEEN_ACCOUNTS_MIN = int(os.getenv('DELAY_BETWEEN_ACCOUNTS_MIN', 5))
    DELAY_BETWEEN_ACCOUNTS_MAX = int(os.getenv('DELAY_BETWEEN_ACCOUNTS_MAX', 10))
    DELAY_BETWEEN_ACTIONS_MIN = int(os.getenv('DELAY_BETWEEN_ACTIONS_MIN', 3))
    DELAY_BETWEEN_ACTIONS_MAX = int(os.getenv('DELAY_BETWEEN_ACTIONS_MAX', 5))
    LOGIN_RETRY_DELAY = int(os.getenv('LOGIN_RETRY_DELAY', 5))
    LOGIN_RETRIES = int(os.getenv('LOGIN_RETRIES', 3))
except (ValueError, TypeError):
    print("Warning: Invalid number format in .env for delays/retries. Using default values.")
    DELAY_BETWEEN_ACCOUNTS_MIN, DELAY_BETWEEN_ACCOUNTS_MAX = 5, 10
    DELAY_BETWEEN_ACTIONS_MIN, DELAY_BETWEEN_ACTIONS_MAX = 3, 5
    LOGIN_RETRY_DELAY, LOGIN_RETRIES = 5, 3

BASE_URL = "https://voyager.preview.craft-world.gg"
GRAPHQL_URL = f"{BASE_URL}/graphql"
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=AIzaSyDgDDykbRrhbdfWUpm1BUgj4ga7d_-wy_g"
AUTH_PAYLOAD_URL = f"{BASE_URL}/auth/payload"
AUTH_LOGIN_URL = f"{BASE_URL}/auth/login"
SESSION_LOGIN_URL = f"{BASE_URL}/api/1/session/login"
RONIN_CHAIN_ID = "2020"


GET_PROFILE_QUERY = """
query GetProfile($uid: ID!) {
  questPointsLeaderboardByUID(uid: $uid) {
    profile {
      uid
      displayName
      level
      questPoints
      twitterHandle
      rank {
        name
        divisionId
        subRank
      }
      equipment {
        slot
        level
        definitionId
      }
    }
    position
    coinRewardAmount
  }
}
"""
ACCOUNT_RESOURCES_QUERY = """
query AccountResources {
  account {
    resources {
      symbol
      amount
    }
  }
}
"""
FULL_REFERRAL_QUERY="query GetReferralProfile{account{profile{referralAccount{code maxRecruits recruits{profile{uid displayName}availablePoints hasReceivedBonus}}}}}"
QUEST_PROGRESS_QUERY="query QuestProgress{account{questProgresses{quest{id name reward}status}}}"
COMPLETE_QUEST_MUTATION="mutation CompleteQuest($questId:String!){completeQuest(questId:$questId){success}}"
LINK_TO_INVITER_MUTATION="mutation LinkToInviter($inviterCode:String!){linkToInviter(inviterCode:$inviterCode){success}}"
CLAIM_RECRUIT_POINTS_MUTATION="mutation ClaimRecruitPoints($uid:ID!){claimRecruitPoints(uid:$uid){questPoints recruit{availablePoints}}}"
CLAIM_INITIAL_RECRUIT_REWARDS_MUTATION="mutation ClaimInitialRecruitRewards{claimInitialRecruitRewards{success}}"
GET_SHOP_CHESTS_QUERY="query GetShopChests{account{getShopChests{id name dailyPurchases dailyLimit price{unit}}}}"
BUY_AND_OPEN_CHEST_MUTATION="mutation BuyAndOpenChestMutation($chestId:String!){buyAndOpenChest(chestId:$chestId){crystals equipment{name tier}}}"
