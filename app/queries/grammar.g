%import common.LETTER
%import common.DIGIT
%import common.WS_INLINE

TAG: (LETTER | DIGIT | "_")+
TYPE: LETTER+

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

metatag: TAG ":" TYPE -> metatag
        | "-" metatag -> negation
