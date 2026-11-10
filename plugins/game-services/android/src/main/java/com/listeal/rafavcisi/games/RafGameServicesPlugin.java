package com.listeal.rafavcisi.games;

import android.content.Intent;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.google.android.gms.games.GamesSignInClient;
import com.google.android.gms.games.PlayGames;
import com.google.android.gms.games.PlayGamesSdk;

/**
 * Google Play Games leaderboards for Raf Avcısı. Stays switched off (available = false)
 * until res/values/games-ids.xml holds the Play Games project id and leaderboard ids,
 * so the app never crashes before Play Console setup is done.
 */
@CapacitorPlugin(name = "RafGameServices")
public class RafGameServicesPlugin extends Plugin {

    private boolean ready = false;

    private String res(String name) {
        int id = getContext().getResources().getIdentifier(name, "string", getContext().getPackageName());
        if (id == 0) return "";
        String v = getContext().getString(id);
        return v == null ? "" : v.trim();
    }

    @Override
    public void load() {
        if (!res("game_services_project_id").matches("\\d+")) return;
        try {
            PlayGamesSdk.initialize(getContext());
            ready = true;
        } catch (Exception e) {
            ready = false;
        }
    }

    private void done(PluginCall call, String key, boolean value) {
        JSObject r = new JSObject();
        r.put(key, value);
        call.resolve(r);
    }

    @PluginMethod
    public void available(PluginCall call) {
        done(call, "available", ready);
    }

    @PluginMethod
    public void signIn(PluginCall call) {
        if (!ready || getActivity() == null) { done(call, "authenticated", false); return; }
        GamesSignInClient client = PlayGames.getGamesSignInClient(getActivity());
        client.isAuthenticated().addOnCompleteListener(t -> {
            boolean ok = t.isSuccessful() && t.getResult() != null && t.getResult().isAuthenticated();
            if (ok || !Boolean.TRUE.equals(call.getBoolean("interactive", false))) { done(call, "authenticated", ok); return; }
            client.signIn().addOnCompleteListener(t2 ->
                done(call, "authenticated", t2.isSuccessful() && t2.getResult() != null && t2.getResult().isAuthenticated()));
        });
    }

    @PluginMethod
    public void submitScore(PluginCall call) {
        String board = res("leaderboard_" + call.getString("leaderboard", ""));
        Integer score = call.getInt("score");
        if (!ready || board.isEmpty() || score == null || getActivity() == null) { done(call, "sent", false); return; }
        PlayGames.getLeaderboardsClient(getActivity()).submitScore(board, score);
        done(call, "sent", true);
    }

    @PluginMethod
    public void showLeaderboard(PluginCall call) {
        String board = res("leaderboard_" + call.getString("leaderboard", ""));
        if (!ready || board.isEmpty() || getActivity() == null) { done(call, "shown", false); return; }
        PlayGames.getLeaderboardsClient(getActivity()).getLeaderboardIntent(board)
            .addOnSuccessListener(intent -> { getActivity().startActivityForResult(intent, 9004); done(call, "shown", true); })
            .addOnFailureListener(e -> done(call, "shown", false));
    }
}
