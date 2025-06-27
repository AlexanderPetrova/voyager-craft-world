from voyager_bot.api.api_client import ApiClient as _Api
import voyager_bot.config as _conf, voyager_bot.logger as _log

async def _profile_stats(client: _Api):
    if not client.uid:
        _log.error("UID not found in session. Please log in again.")
        return

    variables = {"uid": client.uid}
    _res = await client.send_graphql_request(_conf.GET_PROFILE_QUERY, variables)
    if _res is None:
        _log.error("Failed to get a response from the server.")
        return
        
    data = _res.get('data')
    lead_data = data.get('questPointsLeaderboardByUID') if data else None
    if not lead_data:
        _log.error("Failed to retrieve profile data.")
        if _res.get('errors'):
            for err in _res['errors']:
                _log.error(f"Server Error: {err.get('message', 'Message unknown')}")
        return
    
    profile = lead_data.get('profile')
    if not profile:
        _log.error("Profile data was not found in the response")
        return
        
    width = 63
    print(f"\n{_log.C['green']}╔{'═' * (width)}╗{_log.C['reset']}")
    
    title = " Profile Stats "
    print(f"{_log.C['green']}║{_log.C['yellow']}{_log.C['bold']}{title.center(width)}{_log.C['green']}║{_log.C['reset']}")
    print(f"{_log.C['green']}╠{'═' * (width)}╣{_log.C['reset']}")

    def _row(label, value, color=_log.C['yellow']):
        if value is not None:
            value_str = str(value)
            clean_text = f" {label:<15}: {value_str}"
            padding = width - len(clean_text)
            if padding < 0: padding = 0
            
            color_text = f" {label:<15}: {color}{value_str}{_log.C['reset']}"
            print(f"{_log.C['green']}║{color_text}{' ' * padding}║{_log.C['reset']}")

    _row("Display Name", profile.get('displayName'))
    _row("Level", profile.get('level'))
    _row("Quest Points", f"{profile.get('questPoints', 0):,}")
    _row("Twitter", f"@{profile.get('twitterHandle')}" if profile.get('twitterHandle') else "Not connected")
    _row("Leaderboard", f"#{lead_data.get('position', 'N/A'):,}")
    
    rank_info = profile.get('rank')
    if rank_info:
        _row("Current Rank", f"{rank_info.get('name')} ({rank_info.get('subRank')})")
    
    equipment = profile.get('equipment')
    if equipment:
        print(f"{_log.C['green']}╠{'═' * (width)}╣{_log.C['reset']}")
        header = " Equipped Items "
        print(f"{_log.C['green']}║{_log.C['yellow']}{header.center(width)}{_log.C['green']}║{_log.C['reset']}")
        print(f"{_log.C['green']}╠{'═' * (width)}╣{_log.C['reset']}")
        for item in equipment:
            slot = item.get('slot', 'N/A').replace('_', ' ').title()
            level = item.get('level', 0)
            item_id = item.get('definitionId', 'N/A')
            
            value_str = f"Lv. {level:<3} ({item_id})"
            clean_text = f" {slot:<15}: {value_str}"
            padding = width - len(clean_text)
            if padding < 0: padding = 0

            color_text = f" {slot:<15}: {_log.C['green']}{value_str}{_log.C['reset']}"
            print(f"{_log.C['green']}║{color_text}{' ' * padding}║{_log.C['reset']}")
    
    print(f"{_log.C['green']}╚{'═' * (width)}╝{_log.C['reset']}")
