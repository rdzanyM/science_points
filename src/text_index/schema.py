from whoosh import fields


schema = fields.Schema(
    # Identifier of this entry in the respective DB table
    id=fields.ID(stored=True),
    # Name (or names) of this journal/conference/publisher
    name=fields.NGRAMWORDS(queryor=True, stored=True),
    # Names of science domains for this entry
    domains=fields.KEYWORD(commas=True, stored=True),
)
