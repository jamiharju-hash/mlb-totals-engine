insert into public.team_market_features
(as_of_date, team, ml_roi_ytd, rl_roi_ytd, ou_roi_ytd, ml_profit_ytd, rl_profit_ytd, ou_profit_ytd, value_score)
values
(current_date, 'ATL', 0.196, 0.457, -0.052, 6.28, 14.63, -1.50, 0.2893),
(current_date, 'CIN', 0.292, 0.182, 0.104, 9.04, 5.63, 3.10, 0.2088),
(current_date, 'TB', 0.177, 0.237, 0.061, 5.31, 7.12, 1.83, 0.1896)
on conflict (as_of_date, team) do update set
  ml_roi_ytd = excluded.ml_roi_ytd,
  rl_roi_ytd = excluded.rl_roi_ytd,
  ou_roi_ytd = excluded.ou_roi_ytd,
  ml_profit_ytd = excluded.ml_profit_ytd,
  rl_profit_ytd = excluded.rl_profit_ytd,
  ou_profit_ytd = excluded.ou_profit_ytd,
  value_score = excluded.value_score;
