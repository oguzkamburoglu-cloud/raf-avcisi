package com.listeal.rafavcisi.amazon;

import com.amazon.device.iap.PurchasingListener;
import com.amazon.device.iap.PurchasingService;
import com.amazon.device.iap.model.FulfillmentResult;
import com.amazon.device.iap.model.Product;
import com.amazon.device.iap.model.ProductDataResponse;
import com.amazon.device.iap.model.ProductType;
import com.amazon.device.iap.model.PurchaseResponse;
import com.amazon.device.iap.model.PurchaseUpdatesResponse;
import com.amazon.device.iap.model.Receipt;
import com.amazon.device.iap.model.RequestId;
import com.amazon.device.iap.model.UserDataResponse;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.json.JSONArray;

/**
 * Amazon Appstore in-app purchases for the Amazon build of Raf Avcısı.
 * Same method names and result shapes as the parts of @capgo/native-purchases that
 * src/native.js uses, so the game's shop code works unchanged:
 *   getProducts({productIdentifiers}) -> {products:[{identifier, priceString, title}]}
 *   getPurchases()                    -> {purchases:[{productIdentifier, transactionId}]}  (owned entitlements)
 *   purchaseProduct({productIdentifier}) resolves on success, rejects otherwise
 *   restorePurchases()                same as getPurchases
 * Consumables (packs, coins) are reported FULFILLED to Amazon as soon as the purchase succeeds;
 * the game then grants them when the promise resolves.
 */
@CapacitorPlugin(name = "AmazonIap")
public class AmazonIapPlugin extends Plugin implements PurchasingListener {

    private final Map<String, PluginCall> pending = new HashMap<>();
    private final Map<String, List<Receipt>> updates = new HashMap<>();

    @Override
    public void load() {
        PurchasingService.registerListener(getContext().getApplicationContext(), this);
    }

    private synchronized void keep(RequestId id, PluginCall call) {
        if (id == null) { call.reject("Amazon Appstore is not available"); return; }
        pending.put(id.toString(), call);
    }

    private synchronized PluginCall take(RequestId id) {
        return id == null ? null : pending.remove(id.toString());
    }

    @PluginMethod
    public void getProducts(PluginCall call) {
        JSArray ids = call.getArray("productIdentifiers");
        Set<String> skus = new HashSet<>();
        try {
            if (ids != null) for (int i = 0; i < ids.length(); i++) skus.add(ids.getString(i));
        } catch (Exception e) { /* ignore malformed ids */ }
        if (skus.isEmpty()) { JSObject r = new JSObject(); r.put("products", new JSArray()); call.resolve(r); return; }
        keep(PurchasingService.getProductData(skus), call);
    }

    @PluginMethod
    public void purchaseProduct(PluginCall call) {
        String sku = call.getString("productIdentifier");
        if (sku == null || sku.isEmpty()) { call.reject("productIdentifier missing"); return; }
        keep(PurchasingService.purchase(sku), call);
    }

    @PluginMethod
    public void getPurchases(PluginCall call) {
        keep(PurchasingService.getPurchaseUpdates(true), call);
    }

    @PluginMethod
    public void restorePurchases(PluginCall call) {
        keep(PurchasingService.getPurchaseUpdates(true), call);
    }

    @Override
    public void onUserDataResponse(UserDataResponse response) { }

    @Override
    public void onProductDataResponse(ProductDataResponse response) {
        PluginCall call = take(response.getRequestId());
        if (call == null) return;
        if (response.getRequestStatus() != ProductDataResponse.RequestStatus.SUCCESSFUL) {
            call.reject("Product data: " + response.getRequestStatus());
            return;
        }
        JSArray list = new JSArray();
        Map<String, Product> data = response.getProductData();
        if (data != null) {
            for (Product p : data.values()) {
                JSObject o = new JSObject();
                o.put("identifier", p.getSku());
                o.put("priceString", p.getPrice());
                o.put("title", p.getTitle());
                o.put("description", p.getDescription());
                list.put(o);
            }
        }
        JSObject r = new JSObject();
        r.put("products", list);
        call.resolve(r);
    }

    @Override
    public void onPurchaseResponse(PurchaseResponse response) {
        PluginCall call = take(response.getRequestId());
        PurchaseResponse.RequestStatus status = response.getRequestStatus();
        Receipt receipt = response.getReceipt();
        if (status == PurchaseResponse.RequestStatus.SUCCESSFUL && receipt != null && !receipt.isCanceled()) {
            if (receipt.getProductType() == ProductType.CONSUMABLE) {
                PurchasingService.notifyFulfillment(receipt.getReceiptId(), FulfillmentResult.FULFILLED);
            }
            if (call != null) call.resolve(receiptJson(receipt));
            return;
        }
        if (call == null) return;
        if (status == PurchaseResponse.RequestStatus.ALREADY_PURCHASED) {
            // Premium bought before (e.g. on another Fire device): treat as owned
            JSObject r = new JSObject();
            r.put("productIdentifier", call.getString("productIdentifier"));
            r.put("alreadyOwned", true);
            call.resolve(r);
            return;
        }
        call.reject("Purchase: " + status);
    }

    @Override
    public void onPurchaseUpdatesResponse(PurchaseUpdatesResponse response) {
        String key = response.getRequestId() == null ? "" : response.getRequestId().toString();
        if (response.getRequestStatus() != PurchaseUpdatesResponse.RequestStatus.SUCCESSFUL) {
            PluginCall call = take(response.getRequestId());
            synchronized (this) { updates.remove(key); }
            if (call != null) call.reject("Purchase updates: " + response.getRequestStatus());
            return;
        }
        List<Receipt> all;
        synchronized (this) {
            all = updates.get(key);
            if (all == null) { all = new ArrayList<>(); updates.put(key, all); }
            if (response.getReceipts() != null) all.addAll(response.getReceipts());
        }
        if (response.hasMore()) {
            // the next page answers with a new request id: move the waiting call and receipts over
            RequestId next = PurchasingService.getPurchaseUpdates(false);
            synchronized (this) {
                PluginCall call = pending.remove(key);
                List<Receipt> got = updates.remove(key);
                if (next != null) {
                    if (call != null) pending.put(next.toString(), call);
                    updates.put(next.toString(), got);
                } else if (call != null) {
                    call.resolve(purchasesJson(got));
                }
            }
            return;
        }
        PluginCall call = take(response.getRequestId());
        synchronized (this) { updates.remove(key); }
        if (call != null) call.resolve(purchasesJson(all));
    }

    private JSObject receiptJson(Receipt r) {
        JSObject o = new JSObject();
        o.put("productIdentifier", r.getSku());
        o.put("transactionId", r.getReceiptId());
        o.put("productType", String.valueOf(r.getProductType()));
        return o;
    }

    private JSObject purchasesJson(List<Receipt> receipts) {
        JSONArray list = new JSONArray();
        if (receipts != null) {
            for (Receipt r : receipts) {
                if (r.isCanceled()) continue;
                if (r.getProductType() == ProductType.CONSUMABLE) continue; // already fulfilled when bought
                list.put(receiptJson(r));
            }
        }
        JSObject res = new JSObject();
        res.put("purchases", list);
        return res;
    }
}
