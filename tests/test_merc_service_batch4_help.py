from crystal_guild.help_system import help_messages


def test_merc_help_topic_explains_marks_and_contract_rules():
    text = " ".join(help_messages("mercs"))
    assert "Hunt Seals" in text
    assert "not Hunt Seals" in text
    assert "C 1, B 2, A 3, S 5" in text
    assert "consumed only when" in text
    assert "does not refund" in text


def test_merc_help_aliases_route_to_same_topic():
    assert help_messages("merc") == help_messages("mercs")
