%import common.WS_INLINE

TAG: /\w+/
META_VALUE: /[\w.*-]+/

?query: tag
      | metatag
      | or
      | and
      | p_query

p_query: "(" WS_INLINE* query WS_INLINE* ")" -> group
       | "-" p_query -> negation

or: query (WS_INLINE* "+" WS_INLINE* query)+ -> disjunction

and: (tag | metatag | p_query) (WS_INLINE+ (tag | metatag | p_query))+ -> conjunction

tag: TAG -> tag
   | "-" tag -> negation

metatag: TAG ":" META_VALUE -> metatag
        | "-" metatag       -> negation
