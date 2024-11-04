from user_agents import parse as ua_parser


def is_suspected_bot(user_agent):
    user_agent = user_agent or ""
    # ref: https://github.com/ua-parser/uap-core/issues/554
    if "HeadlessChrome" in user_agent:
        return True
    return ua_parser(user_agent).is_bot
