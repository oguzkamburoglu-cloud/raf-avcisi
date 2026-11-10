import Foundation
import Capacitor
import GameKit

/// Game Center for Raf Avcısı: sign in, send a score, show a leaderboard.
/// Leaderboard ids are the ones created in App Store Connect (scripts/asc-gamecenter.py).
@objc(RafGameServicesPlugin)
public class RafGameServicesPlugin: CAPPlugin, CAPBridgedPlugin, GKGameCenterControllerDelegate {
    public let identifier = "RafGameServicesPlugin"
    public let jsName = "RafGameServices"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "available", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "signIn", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "submitScore", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "showLeaderboard", returnType: CAPPluginReturnPromise)
    ]
    private var waiting: [CAPPluginCall] = []
    private var handlerSet = false

    @objc func available(_ call: CAPPluginCall) {
        call.resolve(["available": true, "authenticated": GKLocalPlayer.local.isAuthenticated])
    }

    @objc func signIn(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            let player = GKLocalPlayer.local
            if player.isAuthenticated {
                call.resolve(["authenticated": true])
                return
            }
            self.waiting.append(call)
            if self.handlerSet { return }
            self.handlerSet = true
            player.authenticateHandler = { [weak self] viewController, _ in
                guard let self = self else { return }
                if let viewController = viewController {
                    self.bridge?.viewController?.present(viewController, animated: true)
                    return
                }
                let ok = GKLocalPlayer.local.isAuthenticated
                let calls = self.waiting
                self.waiting = []
                calls.forEach { $0.resolve(["authenticated": ok]) }
            }
        }
    }

    @objc func submitScore(_ call: CAPPluginCall) {
        guard let board = call.getString("leaderboard"), let score = call.getInt("score") else {
            call.reject("leaderboard and score are required")
            return
        }
        guard GKLocalPlayer.local.isAuthenticated else {
            call.resolve(["sent": false])
            return
        }
        GKLeaderboard.submitScore(score, context: 0, player: GKLocalPlayer.local, leaderboardIDs: [board]) { error in
            call.resolve(["sent": error == nil])
        }
    }

    @objc func showLeaderboard(_ call: CAPPluginCall) {
        let board = call.getString("leaderboard") ?? ""
        DispatchQueue.main.async {
            guard GKLocalPlayer.local.isAuthenticated else {
                call.resolve(["shown": false])
                return
            }
            let viewController = board.isEmpty
                ? GKGameCenterViewController(state: .leaderboards)
                : GKGameCenterViewController(leaderboardID: board, playerScope: .global, timeScope: .allTime)
            viewController.gameCenterDelegate = self
            self.bridge?.viewController?.present(viewController, animated: true)
            call.resolve(["shown": true])
        }
    }

    public func gameCenterViewControllerDidFinish(_ gameCenterViewController: GKGameCenterViewController) {
        gameCenterViewController.dismiss(animated: true)
    }
}
