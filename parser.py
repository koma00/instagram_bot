from instagram import WebAgentAccount, Account, Media

account = Account("chook_firs")

agent = WebAgentAccount("koma_second")
agent.auth("VAZ2106")
media = Media("B5avRVIHl0E")
agent.add_comment(media, 'Cool')