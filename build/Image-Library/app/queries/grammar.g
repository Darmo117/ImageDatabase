%import common.LETTER
%import common.DIGIT
%import common.WS_INLINE

TAG: (LETTER | DIGIT | "_")+

%ignore WS_INLINE // ?

?query: tag
      | or
      | and
      | p_query

p_query: "(" query ")" -> group
       | "-" p_query -> negation

or: query ("+" query)+ -> disjunction

and: (tag | p_query)+ -> conjunction

tag: TAG -> tag
   | "-" tag -> negation
