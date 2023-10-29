-- Drop table
DROP TABLE IF EXISTS public.chat_history;

-- Create table
CREATE TABLE public.chat_history(
  uuid uuid PRIMARY KEY,
  user_id varchar NOT NULL,
  title varchar NOT NULL,
  histories json NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);
